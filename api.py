from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import data
import evals
import agent
from agent import run_scenario

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=['http://localhost:5173'],
    allow_methods=['*'],
    allow_headers=["*"]
    )

class RunRequest(BaseModel):
    recommended_qty:int


@app.get("/state")
def get_state():

    return{
        "product":data.PRODUCT,
        "inventory":data.INVENTORY,
        "demand":data.DEMAND,
        "open_pos":data.OPEN_POS,
        "suppliers":data.SUPPLIERS,
        "budget":data.BUDGET,
        "storage":data.STORAGE,
        "created_pos":data.CREATED_POS,
    }

@app.post("/run")
def run(req:RunRequest):
    return run_scenario(req.recommended_qty)

@app.post("/evals")
def run_evals():
    rows = evals.run_all()
    return {"rows": rows, "passed": sum(r["passed"] for r in rows), "total": len(rows)}

@app.get("/scenarios")
def list_scenarios():
    return list(data.SCENARIOS.keys())

@app.post("/admin/scenario/{name}")
def set_scenario(name: str):
    if name not in data.SCENARIOS:
        raise HTTPException(404, f"unknown scenario '{name}'")
    data.apply_scenario(name)
    return {"applied": name}

@app.post("/approve")
def approve():
    return agent.approve_run()

@app.post("/reject")
def reject():
    return agent.reject_run()
