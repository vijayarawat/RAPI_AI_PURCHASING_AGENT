import os
import json
from dotenv import load_dotenv
from google import genai
from google.genai import types

import data
import tools
import validator

load_dotenv()
client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
APPROVAL_VALUE_THRESHOLD = int(os.environ.get("APPROVAL_VALUE_THRESHOLD", 500))

TOOL_MAP = {f.__name__: f for f in tools.TOOLS}

PENDING = None  # decision + tool_calls awaiting human approval, if any

SYSTEM_PROMPT = """
You are a purchasing agent for a retail company. You receive a situation (for example a system purchase recommendation) and decide what to do.
Rules:
- A system recommendation is a hypothesis, not an instruction. Never trust it blindly.
- Investigate using the tools before deciding: check inventory, demand, open purchase orders,
  supplier terms, budget and storage.
- If forecast_age_days from get_demand_forecast is greater than 7, the forecast is too stale
  to trust. Decide "investigate" instead of accept/modify/reject, regardless of the calculated need.
- Use calc_net_need with a supplier's lead time to find the real quantity needed before proposing one.

When done investigating, reply with ONLY this JSON, no other text, no markdown fences:
{"decision": "accept|modify|reject|investigate",
 "supplier": "<supplier id or null>",
 "quantity": <int or null>,
 "reasoning": "<short explanation of the factors behind the decision>"}
"""


def _result(decision, tool_calls, **extra):
    base = {"decision": decision, "tool_calls": tool_calls, "preflight_violations": None,
            "po": None, "verification_problems": None, "status": None, "value": None}
    base.update(extra)
    return base


def _execute_and_verify(decision, tool_calls, status_on_success="success"):
    supplier, qty = decision["supplier"], decision["quantity"]
    po = validator.execute_po(supplier, qty)
    expected = tools.calc_net_need(data.SUPPLIERS[supplier]["lead_time_days"])["net_need"]
    problems = validator.verify_result(po, expected_net_need=expected)
    status = status_on_success if not problems else "verification_failed"
    return _result(decision, tool_calls, po=po, verification_problems=problems, status=status)


def run_scenario(recommended_qty: int, max_steps: int = 10):
    global PENDING
    prompt = f"{SYSTEM_PROMPT}\n\nThe purchasing system recommends buying {recommended_qty} units. Decide."
    cfg = types.GenerateContentConfig(
        tools=tools.TOOLS,
        automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
    )
    contents = [types.Content(role="user", parts=[types.Part.from_text(text=prompt)])]
    tool_calls = []
    decision = None

    for _ in range(max_steps):
        response = client.models.generate_content(model=MODEL, contents=contents, config=cfg)
        contents.append(response.candidates[0].content)

        if not response.function_calls:
            text = response.text.strip().strip("`")
            if text.startswith("json"):
                text = text[4:]
            decision = json.loads(text[text.index("{"): text.rindex("}") + 1])
            break

        parts = []
        for call in response.function_calls:
            args = dict(call.args or {})
            output = TOOL_MAP[call.name](**args)
            tool_calls.append({"tool": call.name, "args": args})
            payload = output if isinstance(output, dict) else {"result": output}
            parts.append(types.Part.from_function_response(name=call.name, response=payload))
        contents.append(types.Content(role="user", parts=parts))

    if decision is None:
        raise RuntimeError("agent did not reach a decision within the step limit")

    if decision["decision"] not in ("accept", "modify"):
        return _result(decision, tool_calls, status="no_action")

    violations = validator.validate_po(decision["supplier"], decision["quantity"])
    if violations:
        return _result(decision, tool_calls, preflight_violations=violations, status="blocked")

    terms = data.SUPPLIERS[decision["supplier"]]
    value = decision["quantity"] * terms["price_per_unit"]

    if value > APPROVAL_VALUE_THRESHOLD:
        PENDING = {"decision": decision, "tool_calls": tool_calls}
        return _result(decision, tool_calls, status="awaiting_approval", value=value)

    return _execute_and_verify(decision, tool_calls)


def approve_run():
    global PENDING
    if PENDING is None:
        raise RuntimeError("no run is awaiting approval")
    decision, tool_calls = PENDING["decision"], PENDING["tool_calls"]
    PENDING = None

    # Re-validate: budget or storage may have changed while this was waiting.
    violations = validator.validate_po(decision["supplier"], decision["quantity"])
    if violations:
        return _result(decision, tool_calls, preflight_violations=violations, status="blocked")

    return _execute_and_verify(decision, tool_calls)


def reject_run():
    global PENDING
    if PENDING is None:
        raise RuntimeError("no run is awaiting approval")
    decision, tool_calls = PENDING["decision"], PENDING["tool_calls"]
    PENDING = None
    return _result(decision, tool_calls, status="rejected_by_human")


if __name__ == "__main__":
    print(json.dumps(run_scenario(800), indent=2))
