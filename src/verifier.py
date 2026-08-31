#!/usr/bin/env python3
"""
Medical Staff Scheduling Verifier
----------------------------------
Evaluates generated weekly hospital schedules against strict operational and legal constraints.
Acts as the programmatic Ground Truth evaluator for model benchmark outputs.
"""

import json
import sys
from typing import Dict, Any, List, Tuple


class ScheduleVerifier:
    def __init__(self, staff_data: Dict[str, Any], demands_data: Dict[str, Any]):
        self.staff_dict = {doc["id"]: doc for doc in staff_data["staff"]}
        self.demands = demands_data
        self.shift_hours = demands_data.get("shift_hours", 8)
        self.days = demands_data.get("days", ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"])
        self.shifts = demands_data.get("shifts", ["Morning", "Afternoon", "Night"])

    def evaluate(self, schedule: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluates a schedule dictionary.
        Returns:
            Dict containing validation boolean, total hard violations, violation breakdown, and details.
        """
        violations = []
        assigned_hours = {doc_id: 0 for doc_id in self.staff_dict}
        daily_assignments = {doc_id: set() for doc_id in self.staff_dict}

        # Chronological list of shifts to verify rest times
        chronological_shifts: List[Tuple[str, str, List[str]]] = []

        # 1. Structural adherence and basic shift presence
        for day in self.days:
            if day not in schedule:
                violations.append(f"MISSING_DAY: Day {day} is completely missing in schedule.")
                continue

            for shift in self.shifts:
                if shift not in schedule[day]:
                    violations.append(f"MISSING_SHIFT: Shift {shift} on {day} is missing.")
                    continue

                assigned_docs = schedule[day][shift]
                if not isinstance(assigned_docs, list):
                    violations.append(f"INVALID_FORMAT: Shift {day} {shift} is not a list of doctor IDs.")
                    continue

                chronological_shifts.append((day, shift, assigned_docs))

                # Check unique IDs in same shift
                if len(assigned_docs) != len(set(assigned_docs)):
                    violations.append(f"DUPLICATE_IN_SHIFT: Duplicate doctor assigned in {day} {shift}: {assigned_docs}")

                # Verify each doctor existence
                for doc_id in assigned_docs:
                    if doc_id not in self.staff_dict:
                        violations.append(f"UNKNOWN_STAFF: {doc_id} assigned in {day} {shift} does not exist in staff list.")
                    else:
                        assigned_hours[doc_id] += self.shift_hours
                        daily_assignments[doc_id].add(day)

                        # HC6: Unavailability
                        slot_str = f"{day}_{shift}"
                        if slot_str in self.staff_dict[doc_id].get("unavailable", []):
                            violations.append(f"HC6_UNAVAILABLE: {doc_id} ({self.staff_dict[doc_id]['name']}) assigned on requested off-slot {slot_str}.")

                # HC3: Total required staff count
                req_total = self.demands["requirements_per_shift"][shift]["required_total"]
                if len(assigned_docs) != req_total:
                    violations.append(f"HC3_STAFFING_DEMAND: {day} {shift} requires {req_total} staff, but has {len(assigned_docs)}.")

                # HC4: Specialty coverage
                spec_counts = {}
                for doc_id in assigned_docs:
                    if doc_id in self.staff_dict:
                        spec = self.staff_dict[doc_id]["specialty"]
                        spec_counts[spec] = spec_counts.get(spec, 0) + 1

                for req_spec, min_count in self.demands["requirements_per_shift"][shift]["specialty_requirements"].items():
                    actual_count = spec_counts.get(req_spec, 0)
                    if actual_count < min_count:
                        violations.append(f"HC4_SPECIALTY_COVERAGE: {day} {shift} requires at least {min_count} {req_spec}(s), but got {actual_count}.")

        # HC2: No double shifts on same day
        for day in self.days:
            if day not in schedule:
                continue
            day_docs = []
            for shift in self.shifts:
                if shift in schedule[day] and isinstance(schedule[day][shift], list):
                    for doc_id in schedule[day][shift]:
                        if doc_id in day_docs:
                            violations.append(f"HC2_NO_DOUBLE_SHIFT: Doctor {doc_id} assigned to multiple shifts on {day}.")
                        day_docs.append(doc_id)

        # HC1: Minimum rest periods between consecutive shifts
        # Consecutive forbidden sequences: Night(day_t) -> Morning(day_t+1) or Afternoon(day_t+1)
        for i in range(len(chronological_shifts) - 1):
            curr_day, curr_shift, curr_docs = chronological_shifts[i]
            next_day, next_shift, next_docs = chronological_shifts[i + 1]

            if curr_shift == "Night" and next_shift in ["Morning", "Afternoon"]:
                overlap = set(curr_docs).intersection(set(next_docs))
                for doc_id in overlap:
                    violations.append(f"HC1_MIN_REST: Doctor {doc_id} worked Night ({curr_day}) and was assigned immediately to {next_shift} ({next_day}) without required rest.")

        # HC5: Maximum weekly legal hours
        for doc_id, hours in assigned_hours.items():
            max_h = self.staff_dict[doc_id]["max_weekly_hours"]
            if hours > max_h:
                violations.append(f"HC5_MAX_HOURS: {doc_id} ({self.staff_dict[doc_id]['name']}) assigned {hours}h, exceeding max {max_h}h by {hours - max_h}h.")

        is_valid = (len(violations) == 0)
        return {
            "is_valid": is_valid,
            "total_hard_violations": len(violations),
            "assigned_hours_distribution": assigned_hours,
            "violations": violations
        }


def main():
    if len(sys.argv) < 4:
        print("Usage: python verifier.py <staff.json> <demands.json> <schedule.json>")
        sys.exit(1)

    with open(sys.argv[1], 'r', encoding='utf-8') as f:
        staff_data = json.load(f)
    with open(sys.argv[2], 'r', encoding='utf-8') as f:
        demands_data = json.load(f)
    with open(sys.argv[3], 'r', encoding='utf-8') as f:
        schedule_data = json.load(f)

    verifier = ScheduleVerifier(staff_data, demands_data)
    result = verifier.evaluate(schedule_data)

    print("=" * 60)
    print(f"VERIFICATION RESULT: {'PASSED (0 VIOLATIONS)' if result['is_valid'] else 'FAILED'}")
    print(f"Total Hard Constraint Violations: {result['total_hard_violations']}")
    print("=" * 60)
    if result["violations"]:
        print("VIOLATION DETAILS:")
        for idx, v in enumerate(result["violations"], 1):
            print(f"  [{idx}] {v}")
    print("=" * 60)


if __name__ == "__main__":
    main()
