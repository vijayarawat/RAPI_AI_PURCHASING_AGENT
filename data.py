import copy

PRODUCT = {
    "sku": "SKU-1001",
    "case_pack": 10,
}

_DEFAULTS = {
    "INVENTORY": {"on_hand": 5000},
    "DEMAND": {"daily_demand": 10, "forecast_age_days": 1},
    "OPEN_POS": [{"po_id": "PO-900", "qty": 600, "arrives_in_days": 5}],
    "SUPPLIERS": {
        "SUP-A": {"lead_time_days": 5, "moq": 100, "price_per_unit": 10},
        "SUP-B": {"lead_time_days": 7, "moq": 50, "price_per_unit": 11},
    },
    "BUDGET": {"available": 10000},
    "STORAGE": {"available_units": 500},
}

# Named presets. Each overrides only the fields that change from _DEFAULTS.
# Try the paired recommended_qty against each to see a different decision.
SCENARIOS = {
    "oversupplied": {
        # _DEFAULTS as-is: open PO already covers all demand over any lead time.
        # recommended_qty=800 -> expect "reject" (true need is 0).
    },
    "understocked": {
        "INVENTORY": {"on_hand": 0},
        "OPEN_POS": [],
        # recommended_qty=100 -> expect "accept" (SUP-A, qty 100 matches need exactly).
    },
    "below_moq": {
        "INVENTORY": {"on_hand": 30},
        "OPEN_POS": [],
        # recommended_qty=70 -> expect "modify" (true need 70 is below SUP-A's MOQ 100).
    },
    "budget_cap": {
        "INVENTORY": {"on_hand": 10},
        "OPEN_POS": [],
        "BUDGET": {"available": 300},
        # recommended_qty=90 -> expect "reject"/"investigate" (nothing fits the budget).
    },
    "storage_cap": {
        "INVENTORY": {"on_hand": 10},
        "OPEN_POS": [],
        "STORAGE": {"available_units": 20},
        # recommended_qty=90 -> expect "reject"/"investigate" (nothing fits storage).
    },
    "stale_forecast": {
        "INVENTORY": {"on_hand": 0},
        "OPEN_POS": [],
        "DEMAND": {"daily_demand": 20, "forecast_age_days": 15},
        # recommended_qty=100 -> expect "investigate" (forecast too old to trust).
    },
}

CREATED_POS = []  # the agent appends here when it actually creates a PO


def reset(overrides=None):
    """Reset all mutable state to defaults, then apply overrides. The single source of truth."""
    global INVENTORY, DEMAND, OPEN_POS, SUPPLIERS, BUDGET, STORAGE, CREATED_POS
    state = copy.deepcopy(_DEFAULTS)
    for key, value in (overrides or {}).items():
        state[key] = value
    INVENTORY = state["INVENTORY"]
    DEMAND = state["DEMAND"]
    OPEN_POS = state["OPEN_POS"]
    SUPPLIERS = state["SUPPLIERS"]
    BUDGET = state["BUDGET"]
    STORAGE = state["STORAGE"]
    CREATED_POS = []


def apply_scenario(name):
    """Reset to a named preset from SCENARIOS. Convenience for manual demos."""
    reset(SCENARIOS[name])


reset()  # initialize live state from defaults on import
