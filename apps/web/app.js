const apiBase = window.KALSHI_API_BASE_URL || "http://localhost:8000";
const samplePayloads = [
  {
    type: "orderbook",
    ticker: "KXTEST-26",
    ts: "2026-01-01T00:00:00+00:00",
    yes_bids: [[40, 20]],
    yes_asks: [[42, 20]],
  },
  {
    type: "price",
    ticker: "KXTEST-26",
    ts: "2026-01-01T00:00:00+00:00",
    last_price: 41,
  },
  {
    type: "settlement",
    ticker: "KXTEST-26",
    ts: "2026-01-02T00:00:00+00:00",
    result: "yes",
  },
];

function byId(id) {
  return document.getElementById(id);
}

function setStatus(message, isError = false) {
  const status = byId("status");
  status.textContent = message;
  status.className = `status ${isError ? "warn" : "good"}`;
}

function setJson(id, value) {
  byId(id).textContent = typeof value === "string" ? value : JSON.stringify(value, null, 2);
}

async function loadDatasets() {
  const response = await fetch(`${apiBase}/datasets`);
  if (!response.ok) throw new Error(await response.text());
  const body = await response.json();
  byId("dataset-list").textContent = body.datasets.length ? body.datasets.join(", ") : "none loaded";
}

async function createDataset() {
  const datasetId = byId("dataset-id").value;
  setStatus("Creating replay dataset...");
  try {
    const response = await fetch(`${apiBase}/datasets`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ dataset_id: datasetId, payloads: samplePayloads, source: "ui-sample" }),
    });
    if (!response.ok) throw new Error(await response.text());
    await loadDatasets();
    setStatus(`Created dataset ${datasetId}`);
  } catch (error) {
    setStatus(`Failed to create dataset: ${error}`, true);
  }
}

async function runDemoBacktest() {
  setStatus("Running replay-backed demo...");
  try {
    const response = await fetch(`${apiBase}/backtests/run-demo`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ payloads: samplePayloads, starting_cash_cents: 10000 }),
    });
    if (!response.ok) throw new Error(await response.text());
    setJson("backtest-result", await response.json());
    setStatus("Demo backtest complete");
  } catch (error) {
    setStatus(`Failed to run backtest: ${error}`, true);
  }
}

async function migrateProject() {
  const fileInput = byId("strategy-file");
  const file = fileInput.files[0];
  if (!file) return;
  setStatus("Uploading strategy project...");
  try {
    const formData = new FormData();
    formData.append("file", file);
    const response = await fetch(`${apiBase}/strategies/migrate`, {
      method: "POST",
      body: formData,
    });
    if (!response.ok) throw new Error(await response.text());
    setJson("migration-report", await response.json());
    setStatus("Migration report generated");
  } catch (error) {
    setStatus(`Failed to migrate strategy: ${error}`, true);
  }
}

byId("create-dataset").addEventListener("click", createDataset);
byId("refresh-datasets").addEventListener("click", () => {
  loadDatasets().catch((error) => setStatus(String(error), true));
});
byId("run-demo").addEventListener("click", runDemoBacktest);
byId("migrate-project").addEventListener("click", migrateProject);
byId("strategy-file").addEventListener("change", (event) => {
  const file = event.target.files[0];
  byId("selected-file").textContent = file ? file.name : "none";
  byId("migrate-project").disabled = !file;
});
