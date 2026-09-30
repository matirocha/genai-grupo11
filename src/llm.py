#!/usr/bin/env python3
"""
Carga del modelo y generación (Hugging Face transformers)
---------------------------------------------------------
- Modelo por defecto: meta-llama/Llama-3.2-3B-Instruct (candidato de Deliverable 1) cuantizado a 4-bit NF4 (bitsandbytes).
  Requiere aceptar la licencia de Meta en Hugging Face e iniciar sesión con `hf auth login`.
- Decodificación greedy (determinista) en todas las estrategias.
- Decodificación restringida: `generate(..., allowed=[...])` limita la salida a una de las cadenas
  permitidas mediante un trie de tokens aplicado como LogitsProcessor (los demás logits -> -inf).
"""

import time
from typing import Dict, List, Optional

import torch
from transformers import (AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig, LogitsProcessor,
                          LogitsProcessorList, TextStreamer)

DEFAULT_MODEL = "meta-llama/Llama-3.2-3B-Instruct"
# Revisiones exactas (commit de Hugging Face) con las que se generaron los resultados de results/
REVISIONS = {
    "Qwen/Qwen2.5-3B-Instruct": "aa8e72537993ba99e69dfaafa59ed015b17504d1",
    "Qwen/Qwen2.5-1.5B-Instruct": "989aa7980e4cf806f80c7fef2b1adb7bc71aa306",
    "Qwen/Qwen2.5-0.5B-Instruct": "7ae557604adf67be50417f59c2c2f167def9a775",
    "microsoft/Phi-3.5-mini-instruct": "2fe192450127e6a83f7441aef6e3ca586c338b77",
    "meta-llama/Llama-3.2-3B-Instruct": "0cb88a4f764b7a12671c53f0838cd831a0843b95",  # requiere aceptar la licencia de Meta
}


class TrieConstraint(LogitsProcessor):
    """Permite solo continuaciones que sigan alguna de las secuencias de tokens del trie."""

    END = -1

    def __init__(self, sequences: List[List[int]], prompt_len: int, stop_ids: List[int]):
        self.root: Dict = {}
        for seq in sequences:
            node = self.root
            for t in seq:
                node = node.setdefault(t, {})
            node[self.END] = {}
        self.prompt_len = prompt_len
        self.stop_ids = stop_ids

    def __call__(self, input_ids: torch.LongTensor, scores: torch.FloatTensor) -> torch.FloatTensor:
        node = self.root
        for t in input_ids[0, self.prompt_len:].tolist():
            node = node.get(t, {})
        allowed = [t for t in node if t != self.END] + (self.stop_ids if self.END in node else [])
        mask = torch.full_like(scores, float("-inf"))
        if allowed:
            mask[0, allowed] = 0.0
        return scores + mask


class LLM:
    def __init__(self, model_id: str = DEFAULT_MODEL, quant: str = "nf4", revision: Optional[str] = None):
        self.model_id = model_id
        self.quant = quant
        revision = revision or REVISIONS.get(model_id)
        t0 = time.time()
        self.tok = AutoTokenizer.from_pretrained(model_id, revision=revision)
        if not torch.cuda.is_available():
            raise RuntimeError("Se requiere GPU CUDA (RTX 5060 local o T4 en Colab).")
        compute_dtype = torch.bfloat16 if torch.cuda.is_bf16_supported() else torch.float16
        kwargs = {"device_map": "cuda", "revision": revision}
        if quant == "nf4":
            kwargs["quantization_config"] = BitsAndBytesConfig(
                load_in_4bit=True, bnb_4bit_quant_type="nf4", bnb_4bit_compute_dtype=compute_dtype)
        else:
            kwargs["dtype"] = compute_dtype
        self.model = AutoModelForCausalLM.from_pretrained(model_id, **kwargs)
        self.model.eval()
        self.revision = getattr(self.model.config, "_commit_hash", None) or revision
        # Tokens de fin de turno: los del generation_config del modelo + marcadores de chat conocidos
        eos = self.model.generation_config.eos_token_id
        stop = set(eos if isinstance(eos, list) else [eos]) | {self.tok.eos_token_id}
        vocab = self.tok.get_vocab()
        stop |= {vocab[m] for m in ("<|im_end|>", "<|end|>", "<|eot_id|>") if m in vocab}
        self.stop_ids = sorted(t for t in stop if t is not None)
        self.load_seconds = round(time.time() - t0, 1)
        self.vram_gb = round(torch.cuda.memory_allocated() / 1e9, 2)
        self.calls = 0
        self.generated_tokens = 0

    def info(self) -> Dict:
        n = 0
        for p in self.model.parameters():  # en 4-bit, quant_state guarda la forma original del tensor empaquetado
            qs = getattr(p, "quant_state", None)
            n += qs.shape.numel() if qs is not None else p.numel()
        return {"model_id": self.model_id, "revision": self.revision, "quant": self.quant,
                "params_B": round(n / 1e9, 2), "vram_gb_after_load": self.vram_gb,
                "gpu": torch.cuda.get_device_name(0)}

    @torch.no_grad()
    def generate(self, messages: List[Dict[str, str]], max_new_tokens: int = 1500,
                 allowed: Optional[List[str]] = None, stream: bool = False) -> str:
        # date_string fija la fecha que la plantilla de Llama 3.2 inserta en el prompt (sin ella usa la fecha del día);
        # las plantillas de Qwen y Phi no la usan.
        inputs = self.tok.apply_chat_template(messages, add_generation_prompt=True, return_tensors="pt",
                                              return_dict=True, date_string="26 Jul 2024").to(self.model.device)
        prompt_len = inputs["input_ids"].shape[1]
        gen_kwargs = dict(max_new_tokens=max_new_tokens, do_sample=False, temperature=None, top_p=None,
                          top_k=None, eos_token_id=self.stop_ids, pad_token_id=self.tok.eos_token_id)
        if allowed is not None:
            seqs = [self.tok(s, add_special_tokens=False).input_ids for s in allowed]
            gen_kwargs["logits_processor"] = LogitsProcessorList([TrieConstraint(seqs, prompt_len, self.stop_ids)])
            gen_kwargs["max_new_tokens"] = max(len(s) for s in seqs) + 1
        if stream:
            gen_kwargs["streamer"] = TextStreamer(self.tok, skip_prompt=True, skip_special_tokens=True)
        out = self.model.generate(**inputs, **gen_kwargs)
        new_tokens = out[0][prompt_len:]
        self.calls += 1
        self.generated_tokens += int(new_tokens.shape[0])
        return self.tok.decode(new_tokens, skip_special_tokens=True)
