import math

import data
import agent
from eval_cases import CASES


def expected_outcome():
    """Ground truth, computed independently of the agent's own tools/validator."""
    incoming = sum(po["qty"] for po in data.OPEN_POS)
    case_pack = data.PRODUCT["case_pack"]
    best = None
    any_need = False

    for sid, terms in data.SUPPLIERS.items():
        raw_need = max(data.DEMAND["daily_demand"] * terms["lead_time_days"] - data.INVENTORY["on_hand"] - incoming, 0)
        need = math.ceil(raw_need / case_pack) * case_pack if raw_need else 0
        if need > 0:
            any_need = True

        qty = math.ceil(max(need, terms["moq"]) / case_pack) * case_pack
        cost = qty * terms["price_per_unit"]
        feasible = need > 0 and cost <= data.BUDGET["available"] and qty <= data.STORAGE["available_units"]

        if feasible and (best is None or cost < best["cost"]):
            best = {"supplier": sid, "qty": qty, "cost": cost}

    if best:
        return {"po_should_exist": True, **best}
    return {"po_should_exist": False, "reason": "constrained" if any_need else "no_need"}


def run_case(case):
    data.reset(case.get("overrides"))
    budget_before = data.BUDGET["available"]
    storage_before = data.STORAGE["available_units"]

    exp = expected_outcome()
    result = agent.run_scenario(case["recommended_qty"])
    
    if result.get("status") == "awaiting_approval":
        result = agent.approve_run()
    po = result["po"]

    po = result["po"]

    checks = {"action_matches_expectation": (po is not None) == exp["po_should_exist"]}

    if po is not None:
        terms = data.SUPPLIERS[po["supplier"]]
        checks["respects_moq"] = po["qty"] >= terms["moq"]
        checks["respects_case_pack"] = po["qty"] % data.PRODUCT["case_pack"] == 0
        checks["respects_budget"] = po["cost"] <= budget_before
        checks["respects_storage"] = po["qty"] <= storage_before
        checks["validated"] = result["verification_problems"] == []
    else:
        # Nothing was created -> the decision or pre-flight must be the reason, not a crash.
        checks["blocked_for_a_real_reason"] = (
            result["decision"]["decision"] not in ("accept", "modify")
            or bool(result["preflight_violations"])
        )

    passed = all(checks.values())
    return {"name": case["name"], "decision": result["decision"]["decision"],
            "expected_po": exp["po_should_exist"], "po": po, "checks": checks, "passed": passed}


def run_all():
    rows = [run_case(c) for c in CASES]
    data.reset()  # leave state clean afterward, since each case mutates it
    return rows


def main():
    rows = run_all()
    for r in rows:
        print(f"[{'PASS' if r['passed'] else 'FAIL'}] {r['name']}: "
              f"decision={r['decision']} expected_po={r['expected_po']} po={'yes' if r['po'] else 'no'}")
        for check, ok in r["checks"].items():
            print(f"    {'ok ' if ok else 'FAIL'} {check}")
    print(f"\n{sum(r['passed'] for r in rows)}/{len(rows)} passed")



if __name__ == "__main__":
    main()
