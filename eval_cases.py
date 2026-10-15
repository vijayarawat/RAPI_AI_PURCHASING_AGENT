CASES = [
    {
        # Open PO already covers all demand over the lead time -> true need is 0.
        # The agent must not blindly accept the 800-unit recommendation.
        "name": "double_count",
        "overrides": {},
        "recommended_qty": 800,
    },
    {
        # Real need is below SUP-A's MOQ (100). Must round up to MOQ or switch supplier.
        "name": "moq_adjustment",
        "overrides": {"INVENTORY": {"on_hand": 30}, "OPEN_POS": []},
        "recommended_qty": 70,
    },
    {
        # Real need exists, but budget is too small for any supplier's minimum order.
        "name": "budget_cap",
        "overrides": {"INVENTORY": {"on_hand": 10}, "OPEN_POS": [], "BUDGET": {"available": 300}},
        "recommended_qty": 90,
    },
    {
        # Real need exists, but storage is too small for any supplier's minimum order.
        "name": "storage_cap",
        "overrides": {"INVENTORY": {"on_hand": 10}, "OPEN_POS": [], "STORAGE": {"available_units": 20}},
        "recommended_qty": 90,
    },
]
