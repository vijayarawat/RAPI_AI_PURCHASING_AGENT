import { useState, useEffect } from "react";
import "./App.css";

const API_BASE = "http://localhost:8000";

const DECISION_CLASS = {
  accept: "badge-accept",
  modify: "badge-modify",
  reject: "badge-reject",
  investigate: "badge-investigate",
};

function Badge({ text, cls }) {
  return <span className={`badge ${cls || "badge-default"}`}>{text}</span>;
}

export default function App() {
  const [state, setState] = useState(null);
  const [qty, setQty] = useState(800);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const [evalRows, setEvalRows] = useState(null);
  const [evalSummary, setEvalSummary] = useState(null);
  const [evalLoading, setEvalLoading] = useState(false);
  const [showToolCalls, setShowToolCalls] = useState(false);

  const [scenarios, setScenarios] = useState([]);
  const [selectedScenario, setSelectedScenario] = useState("");
  const [scenarioLoading, setScenarioLoading] = useState(false);

  const [approving, setApproving] = useState(false);

  const loadState = async () => {
    const res = await fetch(`${API_BASE}/state`);
    setState(await res.json());
  };

  // useEffect(() => { loadState(); }, []);
  
  const loadScenarios = async () => {
  const res = await fetch(`${API_BASE}/scenarios`);
  const names = await res.json();
  setScenarios(names);
  if (names.length > 0) setSelectedScenario(names[0]);
  };

  useEffect(() => { loadState(); loadScenarios(); }, []);


  const runScenario = async () => {
    setLoading(true);
    setError(null);
    setResult(null);
    setShowToolCalls(false);
    try {
      const res = await fetch(`${API_BASE}/run`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ recommended_qty: Number(qty) }),
      });
      if (!res.ok) throw new Error(await res.text());
      setResult(await res.json());
      await loadState();
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  const applyScenario = async () => {
  setScenarioLoading(true);
  setError(null);
  try {
    const res = await fetch(`${API_BASE}/admin/scenario/${selectedScenario}`, { method: "POST" });
    if (!res.ok) throw new Error(await res.text());
    await loadState();
  } catch (e) {
    setError(e.message);
  } finally {
    setScenarioLoading(false);
  }
};

const approveRun = async () => {
  setApproving(true);
  setError(null);
  try {
    const res = await fetch(`${API_BASE}/approve`, { method: "POST" });
    if (!res.ok) throw new Error(await res.text());
    setResult(await res.json());
    await loadState();
  } catch (e) {
    setError(e.message);
  } finally {
    setApproving(false);
  }
};

const rejectRun = async () => {
  setApproving(true);
  setError(null);
  try {
    const res = await fetch(`${API_BASE}/reject`, { method: "POST" });
    if (!res.ok) throw new Error(await res.text());
    setResult(await res.json());
  } catch (e) {
    setError(e.message);
  } finally {
    setApproving(false);
  }
};

  const runEvals = async () => {
    setEvalLoading(true);
    setEvalRows(null);
    setEvalSummary(null);
    try {
      const res = await fetch(`${API_BASE}/evals`, { method: "POST" });
      if (!res.ok) throw new Error(await res.text());
      const data = await res.json();
      setEvalRows(data.rows);
      setEvalSummary({ passed: data.passed, total: data.total });
      await loadState(); // evals leave state reset to defaults when done
    } catch (e) {
      setError(e.message);
    } finally {
      setEvalLoading(false);
    }
  };

  return (
    <div className="app">
      <header className="app-header">
        <h1>AI Purchasing Agent</h1>
        <p className="subtitle">Reviews a purchase recommendation, decides, acts, and verifies the result.</p>
      </header>

      <section className="section">
        <div style={{ marginBottom: 12 }}>
  <label>
    Preset:{" "}
    <select value={selectedScenario} onChange={(e) => setSelectedScenario(e.target.value)}>
      {scenarios.map((name) => (
        <option key={name} value={name}>{name}</option>
      ))}
    </select>
  </label>
  <button onClick={applyScenario} disabled={scenarioLoading} style={{ marginLeft: 12 }}>
    {scenarioLoading ? "Applying..." : "Apply scenario"}
  </button>
</div>

        <h2>Current state</h2>

        {!state ? (
          <p>Loading...</p>
        ) : (
          <div className="card">
            <table>
              <tbody>
                <tr><td>On-hand inventory</td><td>{state.inventory.on_hand}</td></tr>
                <tr><td>Daily demand</td><td>{state.demand.daily_demand}</td></tr>
                <tr>
                  <td>Open POs</td>
                  <td>
                    {state.open_pos.length === 0 ? "none" : state.open_pos.map(
                      (po) => `${po.qty} units in ${po.arrives_in_days}d`
                    ).join(", ")}
                  </td>
                </tr>
                <tr>
                  <td>Suppliers</td>
                  <td>
                    {Object.entries(state.suppliers).map(([id, s]) => (
                      <div key={id}>
                        {id}: lead {s.lead_time_days}d, MOQ {s.moq}, ${s.price_per_unit}/unit
                      </div>
                    ))}
                  </td>
                </tr>
                <tr><td>Budget available</td><td>${state.budget.available}</td></tr>
                <tr><td>Storage available</td><td>{state.storage.available_units} units</td></tr>
                <tr><td>POs created so far</td><td>{state.created_pos.length}</td></tr>
              </tbody>
            </table>
          </div>
        )}
      </section>

      <section className="section">
        <h2>Run a scenario</h2>
        <label>
          Recommended quantity:{" "}
          <input type="number" value={qty} onChange={(e) => setQty(e.target.value)} />
        </label>
        <button onClick={runScenario} disabled={loading} style={{ marginLeft: 12 }}>
          {loading ? "Running..." : "Run"}
        </button>
      </section>

      {error && <p className="text-error">Error: {error}</p>}

      {result && (
        <section className="section">
          <h2>Result</h2>

          <p>
            <Badge text={result.decision.decision} cls={DECISION_CLASS[result.decision.decision]} />
            {result.decision.supplier && <> &nbsp; supplier: {result.decision.supplier}</>}
            {result.decision.quantity != null && <> &nbsp; quantity: {result.decision.quantity}</>}
          </p>
          <p><em>{result.decision.reasoning}</em></p>
          {result.tool_calls && result.tool_calls.length > 0 && (
        <>
            <button onClick={() => setShowToolCalls((v) => !v)} style={{ marginBottom: 8 }}>
              {showToolCalls ? "Hide tool calls" : `Show tool calls (${result.tool_calls.length})`}
            </button>

            {showToolCalls && (
              <table className="tool-calls-table">
                <thead>
                  <tr><th>No.</th><th>Tool</th><th>Args</th></tr>
                </thead>
                <tbody>
                  {result.tool_calls.map((t, i) => (
                    <tr key={i}>
                      <td>{i + 1}</td>
                      <td>{t.tool}</td>
                      <td>{Object.entries(t.args).map(([k, v]) => `${k}=${v}`).join(", ") || "—"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </>
        )}

          {result.preflight_violations && (
            <>
              <h3 className="text-warn">Pre-flight violations</h3>
              <ul>{result.preflight_violations.map((v, i) => <li key={i}>{v}</li>)}</ul>
            </>
          )}

          {result.status === "awaiting_approval" && (
  <div className="card approval-card">
    <h3 className="text-warn">Needs approval</h3>
    <p>Order value ${result.value} exceeds the approval threshold (${/* threshold shown for context */ 500}). A human must approve before it's placed.</p>
    <button onClick={approveRun} disabled={approving}>Approve</button>
    <button onClick={rejectRun} disabled={approving} style={{ marginLeft: 8 }}>Reject</button>
  </div>
)}

{result.status === "rejected_by_human" && (
  <p className="text-bad">Rejected by human reviewer. No PO was created.</p>
)}


          {result.po && (
            <>
              <h3 className="text-good">Created PO</h3>
              <p>
                {result.po.po_id}: {result.po.qty} units from {result.po.supplier},
                cost ${result.po.cost}, status {result.po.status}
              </p>
            </>
          )}

          {result.verification_problems && result.verification_problems.length > 0 && (
            <>
              <h3 className="text-bad">Verification problems</h3>
              <ul>{result.verification_problems.map((p, i) => <li key={i}>{p}</li>)}</ul>
            </>
          )}

          {result.po && (!result.verification_problems || result.verification_problems.length === 0) && (
            <p className="text-good">Verified: outcome matches expectation.</p>
          )}
        </section>
      )}

      <section className="section">
  <h2>Evaluation</h2>
  <button onClick={runEvals} disabled={evalLoading}>
    {evalLoading ? "Running evals..." : "Run evals"}
  </button>

  {evalSummary && (
    <p style={{ marginTop: 12 }}>
      <strong>{evalSummary.passed}/{evalSummary.total} passed</strong>
    </p>
  )}

  {evalRows && (
    <table className="eval-table">
      <thead>
        <tr>
          <th>Status</th>
          <th>Case</th>
          <th>Decision</th>
          <th>Expected PO</th>
          <th>PO created</th>
          <th>Checks</th>
        </tr>
      </thead>
      <tbody>
        {evalRows.map((r) => (
          <tr key={r.name} className={r.passed ? "eval-row-pass" : "eval-row-fail"}>
            <td>{r.passed ? "PASS" : "FAIL"}</td>
            <td>{r.name}</td>
            <td>{r.decision}</td>
            <td>{String(r.expected_po)}</td>
            <td>{r.po ? "yes" : "no"}</td>
            <td>
              <ul className="eval-checks">
                {Object.entries(r.checks).map(([check, ok]) => (
                  <li key={check}>{ok ? "ok" : "FAIL"} — {check}</li>
                ))}
              </ul>
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  )}
</section>

    </div>
  );
}
