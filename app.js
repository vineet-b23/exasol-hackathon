/* =========================================================
   BASE CONFIGURATION
   ========================================================= */
const API_BASE_URL = 'https://exasol-hackathon.onrender.com/api/v1';

/* =========================================================
   DOM ELEMENTS
   ========================================================= */
const heroSearch    = document.getElementById("hero-search");
const stepperWrap   = document.getElementById("stepper-wrap");
const stepperQuery  = document.getElementById("stepper-query");
const stepEls       = Array.from(document.querySelectorAll(".step"));
const resultsWrap   = document.getElementById("results");

let currentInvestigation = null;
let challenged = false;
const SCORE_CIRC = 169.6;

/* =========================================================
   SEARCH FORM SUBMIT
   ========================================================= */
document.getElementById("search-form").addEventListener("submit", e => {
  e.preventDefault();
  const val = document.getElementById("search-input").value.trim();
  if (!val) return;
  startInvestigation(val);
});

document.querySelectorAll(".pill").forEach(pill => {
  pill.addEventListener("click", () => startInvestigation(pill.textContent.trim()));
});

/* =========================================================
   INVESTIGATION FETCH
   ========================================================= */
async function startInvestigation(displayQuery) {
  heroSearch.classList.add("hidden");
  resultsWrap.classList.add("hidden");
  stepperWrap.classList.remove("hidden");
  stepperQuery.textContent = `"${displayQuery}"`;

  try {
    const response = await fetch(`${API_BASE_URL}/investigate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query: displayQuery })
    });

    if (!response.ok) throw new Error(`Server status ${response.status}`);

    const data = await response.json();
    
    stepperWrap.classList.add("hidden");
    renderResults(data);
    resultsWrap.classList.remove("hidden");

  } catch (error) {
    stepperWrap.classList.add("hidden");
    heroSearch.classList.remove("hidden");
    alert("Investigation Error: " + error.message);
  }
}

/* =========================================================
   RENDER ENGINE RESULTS
   ========================================================= */
function renderResults(data) {
  currentInvestigation = data;
  challenged = false;

  // 1. Set Title & Summary directly from API
  document.getElementById("finding-title").textContent = data.title || `Investigation: ${data.query}`;
  document.getElementById("finding-summary").textContent = data.summary || "Query execution completed.";

  // 2. Set Confidence Score
  const score = data.score ?? 75;
  document.getElementById("score-num").textContent = score;
  const offset = SCORE_CIRC * (1 - score / 100);
  const ring = document.getElementById("score-ring-fill");
  if (ring) ring.style.strokeDashoffset = offset;

  // 3. Render Evidence Chain & Hypotheses
  const steps = data.hypotheses || [];
  renderChain(steps);
  renderHypotheses(steps);
}

function renderChain(steps) {
  const wrap = document.getElementById("evidence-chain");
  wrap.innerHTML = "";

  if (!steps || steps.length === 0) {
    wrap.innerHTML = `<p style="color:var(--text-muted); padding:12px;">No SQL queries executed.</p>`;
    return;
  }

  steps.forEach((step, idx) => {
    const label = step.hypothesis || `Query ${idx + 1}`;
    const value = `${step.row_count ?? 0} Rows Returned`;

    const el = document.createElement("div");
    el.className = "chain-node";
    el.innerHTML = `
      <span class="chain-node-label">${label}</span>
      <span class="chain-node-value normal">${value}</span>
    `;
    el.addEventListener("click", () => openModal(step));
    wrap.appendChild(el);

    if (idx < steps.length - 1) {
      const conn = document.createElement("div");
      conn.className = "chain-connector";
      conn.innerHTML = `<svg viewBox="0 0 34 14" fill="none"><path d="M0 7H28M22 2L29 7L22 12" stroke="currentColor" stroke-width="1.6"/></svg>`;
      wrap.appendChild(conn);
    }
  });
}

function renderHypotheses(steps) {
  const body = document.getElementById("hyp-table-body");
  body.innerHTML = "";

  steps.forEach((step, idx) => {
    const tr = document.createElement("tr");
    if (idx === 0) tr.classList.add("leading");

    tr.innerHTML = `
      <td>${step.hypothesis || "Hypothesis Analysis"}</td>
      <td class="hyp-score">${step.score ?? (idx === 0 ? 80 : 30)}%</td>
      <td>${step.error ? "Error: " + step.error : `SQL executed (${step.row_count ?? 0} rows)`}</td>
      <td><span class="hyp-status ${idx === 0 ? 'leading' : 'ruled_out'}">${idx === 0 ? "Leading" : "Ruled Out"}</span></td>
    `;
    body.appendChild(tr);
  });
}

/* =========================================================
   DYNAMIC NODE MODAL (SQL + REAL RESULTS)
   ========================================================= */
const modalOverlay = document.getElementById("node-modal");

function openModal(step) {
  document.getElementById("modal-title").textContent = step.hypothesis || "Evidence Detail";
  document.getElementById("modal-table-name").textContent = "EXASOL MAIN SCHEMA";
  document.getElementById("modal-sql").textContent = step.sql || "SELECT * FROM MAIN.ORDERS;";

  const table = document.getElementById("modal-result-table");
  const cols = step.columns && step.columns.length > 0 ? step.columns : ["INFO"];
  const rows = step.rows && step.rows.length > 0 ? step.rows : [["No rows returned"]];

  const thead = `<thead><tr>${cols.map(c => `<th>${c}</th>`).join("")}</tr></thead>`;
  const tbody = `<tbody>${rows.map(r => {
    const vals = Array.isArray(r) ? r : Object.values(r);
    return `<tr>${vals.map(v => `<td>${v}</td>`).join("")}</tr>`;
  }).join("")}</tbody>`;

  table.innerHTML = thead + tbody;
  modalOverlay.classList.remove("hidden");
}

function closeModal() { modalOverlay.classList.add("hidden"); }
document.getElementById("modal-close")?.addEventListener("click", closeModal);
modalOverlay?.addEventListener("click", e => { if (e.target === modalOverlay) closeModal(); });