import math
import data

def get_inventory()->dict:
    """Return current on-hand inventory for the product."""
    return data.INVENTORY

def get_demand_forecast() -> dict:
    """Return expected daily demand and how many days old the forecast is (forecast_age_days)."""
    return data.DEMAND

def get_open_purchase_orders()->dict:
    return data.OPEN_POS


def get_supplier_terms()->dict:
    return data.SUPPLIERS

def get_budget()->dict:
    return data.BUDGET

def get_storage_capacity() -> dict:
    """Return remaining storage capacity, in units."""
    return data.STORAGE

def calc_net_need(lead_time_days:int)->dict:
    """
    Compute the real quantity needed for a given supplier lead time:
    demand expected during the lead time, minus on-hand inventory,
    minus quantity already incoming from open POs. Rounded up to the
    case pack. Never negative. Call this instead of doing the maths yourself.
    """
    daily_demand = data.DEMAND["daily_demand"]
    on_hand = data.INVENTORY["on_hand"]
    incoming = sum(po["qty"] for po in data.OPEN_POS)

    raw_need = max(daily_demand * lead_time_days - on_hand - incoming, 0)
    case_pack = data.PRODUCT["case_pack"]
    net_need = math.ceil(raw_need / case_pack) * case_pack if raw_need else 0

    return {
        "lead_time_days": lead_time_days,
        "daily_demand": daily_demand,
        "on_hand": on_hand,
        "incoming_open_po_qty": incoming,
        "net_need": net_need,
    }


TOOLS =[

    get_inventory,
    get_demand_forecast,
    get_open_purchase_orders,
    get_supplier_terms,
    get_budget,get_storage_capacity,
    calc_net_need

]