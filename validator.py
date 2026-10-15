import data

def validate_po(supplier:str,qty:int)->list:
    """ Return a list of violation strings; empty means the PO is valid. """
    if supplier not in data.SUPPLIERS:
        return [f"Unknown supplier {supplier}"]

    terms = data.SUPPLIERS[supplier]
    violations =[]

    if qty <=0:
        violations.append("Quantity must be positive")
    
    if qty <terms["moq"]:
        violations.append(f"Quantity {qty} is below supplier MOQ{terms['moq']}")

    if qty%data.PRODUCT["case_pack"]!=0:
        violations.append(f"Quantity {qty} is not a multiple of case pack {data.PRODUCT['case_pack']}")

    cost = qty*terms['price_per_unit']
    
    if cost>data.BUDGET['available']:
        violations.append(f"Cost {cost} exceeds available budget {data.BUDGET['available']}")

    if qty > data.STORAGE["available_units"]:
        violations.append(f"qty {qty} exceeds available storage {data.STORAGE['available_units']}")

    return violations


def execute_po(supplier: str, qty: int) -> dict:
    """Create the PO and update budget/storage, as the real purchasing system would."""
    terms = data.SUPPLIERS[supplier]
    cost = qty * terms["price_per_unit"]

    po = {
        "po_id": f"PO-{len(data.CREATED_POS) + 1000}",
        "supplier": supplier,
        "qty": qty,
        "cost": cost,
        "status": "confirmed",
    }
    data.CREATED_POS.append(po)
    data.BUDGET["available"] -= cost
    data.STORAGE["available_units"] -= qty
    return po


def verify_result(po: dict, expected_net_need: int) -> list:
    """Post-execution check: re-read state and confirm the PO actually solves the need."""
    problems = []
    
    if po["status"] != "confirmed":
        problems.append("PO status is not confirmed")
    
    if po["qty"] < expected_net_need:
        problems.append(f"PO qty {po['qty']} is less than net need {expected_net_need}")
    
    if data.BUDGET["available"] < 0:
        problems.append("budget went negative")
    
    if data.STORAGE["available_units"] < 0:
        problems.append("storage went negative")
    
    return problems