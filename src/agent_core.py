#!/usr/bin/env python3
"""
Infraestructura común del sistema de agentes (Deliverable 3)
------------------------------------------------------------
- Prompts versionados: el prompt de cada agente vive en prompts/<agente>.md, fuera del código. El archivo tiene
  una cabecera (agente, versión) y secciones "## <nombre>". Cada técnica de prompting que se ablaciona es una
  sección, así que quitar una técnica = no incluir su sección (el resto del prompt no cambia).
- Trazas: cada mensaje entre agentes, cada llamada a herramienta y cada respuesta del modelo se registra como un
  evento {de, a, tipo, contenido}. Se guardan en results/traces/<conjunto>/<modelo>/<config>/<instancia>.jsonl.
"""

import hashlib
import json
import os
import re
from typing import Any, Callable, Dict, List, Optional

from instances import BASE_DIR

PROMPTS_DIR = os.path.join(BASE_DIR, "prompts")


class Prompt:
    """Prompt versionado de un agente: cabecera + secciones '## nombre'."""

    def __init__(self, name: str):
        path = os.path.join(PROMPTS_DIR, f"{name}.md")
        with open(path, encoding="utf-8") as f:
            raw = f.read()
        self.name = name
        self.path = os.path.relpath(path, BASE_DIR).replace("\\", "/")
        self.sha = hashlib.sha1(raw.encode("utf-8")).hexdigest()[:10]
        head = re.match(r"---\n(.*?)\n---\n", raw, re.S)
        self.meta = dict(line.split(":", 1) for line in head.group(1).splitlines()) if head else {}
        self.meta = {k.strip(): v.strip() for k, v in self.meta.items()}
        self.version = self.meta.get("version", "?")
        body = raw[head.end():] if head else raw
        self.sections: Dict[str, str] = {}
        for block in re.split(r"^## ", body, flags=re.M)[1:]:
            title, _, text = block.partition("\n")
            self.sections[title.strip()] = text.strip()

    def build(self, include: List[str]) -> str:
        """Concatena las secciones pedidas, en el orden del archivo."""
        return "\n\n".join(text for title, text in self.sections.items() if title in include)

    def info(self) -> Dict[str, str]:
        return {"file": self.path, "version": self.version, "sha": self.sha}


class Trace:
    """Registro de los mensajes del sistema de agentes. `echo` imprime cada evento (lo usa el video)."""

    def __init__(self, echo: Optional[Callable[[str], None]] = None,
                 formatter: Optional[Callable[[Dict[str, Any]], str]] = None):
        self.events: List[Dict[str, Any]] = []
        self.echo = echo
        self.formatter = formatter or self.render

    def log(self, src: str, dst: str, kind: str, content: Any, **extra):
        ev = {"i": len(self.events), "de": src, "a": dst, "tipo": kind, "contenido": content, **extra}
        self.events.append(ev)
        if self.echo:
            line = self.formatter(ev)
            if line:
                self.echo(line)

    @staticmethod
    def render(ev: Dict[str, Any]) -> str:
        content = ev["contenido"]
        if not isinstance(content, str):
            content = json.dumps(content, ensure_ascii=False)
        return f"[{ev['de']} -> {ev['a']}] {ev['tipo']}: {content}"

    def save(self, path: str):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            for ev in self.events:
                f.write(json.dumps(ev, ensure_ascii=False) + "\n")
