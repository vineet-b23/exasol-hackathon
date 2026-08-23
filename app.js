/* =========================================================
   BASE CONFIGURATION
   ========================================================= */
const API_BASE_URL = 'https://exasol-hackathon.onrender.com/api/v1';

/* =========================================================
   STATIC DATA
   ========================================================= */
const mockData = {
  team: [
    {
      name: "Vineet B",
      role: "Team Lead — Backend Creation & Entire Integration",
      linkedin: "https://www.linkedin.com/in/vineet-b-vitchennai/"
    },
    {
      name: "Vikhraman G S",
      role: "Frontend Developer",
      linkedin: "https://www.linkedin.com/in/vikhram-sivakumar-85a289371/"
    },
    {
      name: "Manish N",
      role: "Database Creation & Developer",
      linkedin: "https://www.linkedin.com/in/manish-n-3b4979374/"
    }
  ]
};

const STEP_DELAYS = [500, 650, 900, 750, 650, 500];

/* =========================================================
   STATE / DOM
   ========================================================= */
const heroSearch   = document.getElementById("hero-search");
const stepperWrap   = document.getElementById("stepper-wrap");
const stepperQuery  = document.getElementById("stepper-query");
const stepEls       = Array.from(document.querySelectorAll(".step"));
const resultsWrap    = document.getElementById("results");

let stepperTimer = null;
let currentInvestigation = null;
let challenged = false;
const SCORE_CIRC = 169.6;

/* =========================================================
   FRONTEND CLEANUP
   ---------------------------------------------------------
   Removes the History / Archives UI without touching
   investigation, schema, or backend functionality.
   ========================================================= */
function removeHistoryView(){
  // Remove the History navigation item
  const historyNav = document.querySelector(
    '.nav-item[data-view="view-history"]'
  );

  if (historyNav) {
    historyNav.remove();
  }

  // Remove the History view itself
  const historyView = document.getElementById("view-history");

  if (historyView) {
    historyView.remove();
  }
}

/* =========================================================
   REMOVE EXASOL CONNECTED STATUS PILL
   ---------------------------------------------------------
   This only removes the visual status pill.
   Exasol backend functionality remains untouched.
   ========================================================= */
function removeExasolConnectedPill(){
  const statusPill = document.querySelector(".status-pill");

  if (statusPill) {
    statusPill.remove();
  }
}

/* =========================================================
   NAVIGATION
   ========================================================= */
document.querySelectorAll(".nav-item").forEach(btn => {
  btn.addEventListener("click", () => {
    const targetView = document.getElementById(btn.dataset.view);

    // Safety check so removed/invalid navigation items
    // cannot break the application.
    if (!targetView) return;

    document.querySelectorAll(".nav-item").forEach(b => b.classList.remove("active"));
    btn.classList.add("active");

    document.querySelectorAll(".view").forEach(v => v.classList.remove("active"));
    targetView.classList.add("active");

    if (btn.dataset.view === "view-schema") {
      fetchAndRenderSchema();
    }
  });
});

document.getElementById("btn-new-investigation").addEventListener("click", () => {
  document.querySelectorAll(".nav-item").forEach(b => b.classList.remove("active"));
  document.querySelector('.nav-item[data-view="view-investigate"]').classList.add("active");

  document.querySelectorAll(".view").forEach(v => v.classList.remove("active"));
  document.getElementById("view-investigate").classList.add("active");

  resetToHero();
});

document.getElementById("btn-config").addEventListener("click", () => {
  alert("Configuration: Connected to Exasol SaaS (MAIN Schema)");
});

document.getElementById("btn-export").addEventListener("click", () => {
  window.print();
});

/* =========================================================
   SEARCH + QUICK PILLS
   ========================================================= */
document.getElementById("search-form").addEventListener("submit", e => {
  e.preventDefault();

  const val = document.getElementById("search-input").value.trim();

  if (!val) return;

  startInvestigation(val);
});

document.querySelectorAll(".pill").forEach(pill => {
  pill.addEventListener("click", () => {
    startInvestigation(pill.textContent);
  });
});

function resetToHero(){
  clearTimeout(stepperTimer);

  heroSearch.classList.remove("hidden");
  stepperWrap.classList.add("hidden");
  resultsWrap.classList.add("hidden");

  document.getElementById("search-input").value = "";

  stepEls.forEach(s => s.classList.remove("active", "done"));
}

/* =========================================================
   LIVE API REQUESTS (INVESTIGATE)
   ---------------------------------------------------------
   BACKEND CODE PRESERVED.
   ========================================================= */
async function startInvestigation(displayQuery){
  heroSearch.classList.add("hidden");
  resultsWrap.classList.add("hidden");
  stepperWrap.classList.remove("hidden");

  stepperQuery.textContent = `"${displayQuery}"`;

  stepEls.forEach(s => s.classList.remove("active", "done"));

  let i = 0;
  let isFetching = true;

  function advance(){
    if (i > 0) stepEls[i - 1].classList.remove("active");
    if (i > 0) stepEls[i - 1].classList.add("done");

    if (i < stepEls.length) {
      stepEls[i].classList.add("active");

      const delay = isFetching ? STEP_DELAYS[i] : 200;

      stepperTimer = setTimeout(advance, delay);
      i++;
    } else {
      stepperWrap.classList.add("hidden");
    }
  }

  advance();

  try {
    const response = await fetch(`${API_BASE_URL}/investigate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query: displayQuery })
    });

    if (!response.ok) {
      throw new Error(`Server returned ${response.status}: ${response.statusText}`);
    }

    const data = await response.json();

    isFetching = false;

    clearTimeout(stepperTimer);
    stepperWrap.classList.add("hidden");

    renderResults(data);

    resultsWrap.classList.remove("hidden");

    resultsWrap.scrollIntoView({
      behavior: "smooth",
      block: "start"
    });

  } catch (error) {
    clearTimeout(stepperTimer);

    isFetching = false;
    stepperWrap.classList.add("hidden");
    heroSearch.classList.remove("hidden");

    alert("Error running investigation: " + error.message);
  }
}

/* =========================================================
   RENDER RESULTS
   ========================================================= */
function renderResults(data){
  currentInvestigation = data;
  challenged = false;

  // Title
  document.getElementById("finding-title").textContent =
    data.title || `Investigation: ${data.query}`;

  // Summary
  document.getElementById("finding-summary").innerHTML =
    data.summary || "Analysis completed based on Exasol query execution.";

  // Score
  const score = data.score ?? 75;
  setScore(score);

  // Counter evidence UI reset
  document.getElementById("counter-evidence").classList.add("hidden");

  const challengeBtn = document.getElementById("btn-challenge");

  challengeBtn.disabled = false;

  challengeBtn.innerHTML = `
    <svg viewBox="0 0 20 20" fill="none" width="16" height="16">
      <circle cx="9" cy="9" r="6"
        stroke="currentColor"
        stroke-width="1.6"/>
      <path d="M14 14L18 18"
        stroke="currentColor"
        stroke-width="1.6"
        stroke-linecap="round"/>
    </svg>
    Challenge My Conclusion
  `;

  // Evidence Chain Rendering (uses backend execution steps)
  const hypotheses = data.hypotheses || [];

  renderChain(hypotheses);

  // Competing Hypotheses Rendering
  renderHypotheses(hypotheses);
}

function setScore(score){
  document.getElementById("score-num").textContent = score;

  const offset = SCORE_CIRC * (1 - score / 100);

  const ring = document.getElementById("score-ring-fill");

  ring.style.strokeDashoffset = offset;

  ring.style.stroke =
    score >= 80
      ? "var(--violet-500)"
      : score >= 60
        ? "var(--warning)"
        : "var(--danger)";
}

function renderChain(steps){
  const wrap = document.getElementById("evidence-chain");

  wrap.innerHTML = "";

  if (!steps || steps.length === 0) {
    wrap.innerHTML = `
      <p style="color:var(--text-muted); font-size:13px; padding:12px;">
        No evidence steps recorded for this investigation.
      </p>
    `;

    return;
  }

  steps.forEach((step, idx) => {
    const label =
      step.hypothesis ||
      `Hypothesis Step ${idx + 1}`;

    const rowCount =
      step.row_count ??
      (step.rows ? step.rows.length : 0);

    const value = `${rowCount} Records Found`;

    const cls = step.is_valid
      ? "normal"
      : "danger";

    const el = document.createElement("div");

    el.className = "chain-node";

    el.innerHTML = `
      <span class="chain-node-label">${label}</span>
      <span class="chain-node-value ${cls}">
        ${value}
      </span>
    `;

    el.addEventListener("click", () => openModal(step));

    wrap.appendChild(el);

    if (idx < steps.length - 1){
      const connector = document.createElement("div");

      connector.className = "chain-connector";

      connector.innerHTML = `
        <svg viewBox="0 0 34 14" fill="none">
          <path
            d="M0 7H28M22 2L29 7L22 12"
            stroke="currentColor"
            stroke-width="1.6"
            stroke-linecap="round"
            stroke-linejoin="round"/>
        </svg>
      `;

      wrap.appendChild(connector);
    }
  });
}

function renderHypotheses(hyps){
  const body = document.getElementById("hyp-table-body");

  body.innerHTML = "";

  if (!hyps || hyps.length === 0) {
    body.innerHTML = `
      <tr>
        <td colspan="4"
          style="color:var(--text-muted);
                 text-align:center;
                 padding:16px;">
          No alternate hypotheses evaluated.
        </td>
      </tr>
    `;

    return;
  }

  hyps.forEach((h, idx) => {
    const name =
      h.hypothesis ||
      `Hypothesis ${idx + 1}`;

    const score =
      h.score ??
      (idx === 0 ? 82 : 30);

    const rowCount =
      h.row_count ??
      (h.rows ? h.rows.length : 0);

    const signals =
      h.error
        ? `Error: ${h.error}`
        : `Executed SQL returned ${rowCount} rows`;

    const isLeading = idx === 0;

    const tr = document.createElement("tr");

    if (isLeading) {
      tr.classList.add("leading");
    }

    tr.innerHTML = `
      <td>${name}</td>

      <td class="hyp-score">
        ${score}%
      </td>

      <td>
        ${signals}
      </td>

      <td>
        <span class="hyp-status ${isLeading ? 'leading' : 'ruled_out'}">
          ${isLeading ? "Leading" : "Ruled Out"}
        </span>
      </td>
    `;

    body.appendChild(tr);
  });
}

/* =========================================================
   CHALLENGE MY CONCLUSION
   ---------------------------------------------------------
   BACKEND CODE PRESERVED.
   ========================================================= */
document.getElementById("btn-challenge").addEventListener("click", async function(){
  if (challenged || !currentInvestigation) return;

  const investigationId =
    currentInvestigation.id || "latest";

  challenged = true;

  this.disabled = true;

  this.innerHTML = `
    <svg
      viewBox="0 0 20 20"
      fill="none"
      width="16"
      height="16"
      class="spin-icon">

      <path
        d="M17 10a7 7 0 11-2-4.9"
        stroke="currentColor"
        stroke-width="1.8"
        stroke-linecap="round"/>
    </svg>

    Searching for counter-evidence…
  `;

  try {
    const response = await fetch(
      `${API_BASE_URL}/investigate/${investigationId}/challenge`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      }
    );

    if (!response.ok) {
      throw new Error(
        "Challenge failed to evaluate on server."
      );
    }

    const data = await response.json();

    const updatedScore =
      data.challengedScore ?? 45;

    setScore(updatedScore);

    const ce =
      document.getElementById("counter-evidence");

    ce.innerHTML = `
      <div class="counter-evidence-head">
        <span class="counter-dot"></span>
        <span>Counter-Evidence Discovered</span>
      </div>

      <p>
        ${
          data.counterEvidence ||
          "Counter-analysis indicates localized seasonal variances."
        }
      </p>
    `;

    ce.classList.remove("hidden");

    this.innerHTML = `
      <svg
        viewBox="0 0 20 20"
        fill="none"
        width="16"
        height="16">

        <path
          d="M5 10l3.5 3.5L15 6"
          stroke="currentColor"
          stroke-width="1.8"
          stroke-linecap="round"
          stroke-linejoin="round"/>
      </svg>

      Re-evaluated
    `;

  } catch (err) {
    alert(
      "Error challenging conclusion: " +
      err.message
    );

    this.disabled = false;
    challenged = false;
    this.innerHTML = "Retry Challenge";
  }
});

/* =========================================================
   NODE DETAIL MODAL
   ---------------------------------------------------------
   DYNAMIC DATA MAPPING
   ========================================================= */
const modalOverlay =
  document.getElementById("node-modal");

function openModal(step){
  document.getElementById("modal-title").textContent =
    step.hypothesis ||
    "Evidence Detail";

  document.getElementById("modal-table-name").textContent =
    "EXASOL.MAIN";

  document.getElementById("modal-sql").textContent =
    step.sql ||
    "No SQL Query Logged";

  const table =
    document.getElementById("modal-result-table");

  const columns =
    step.columns &&
    step.columns.length > 0
      ? step.columns
      : ["STATUS"];

  const rows =
    step.rows &&
    step.rows.length > 0
      ? step.rows
      : [["No rows returned"]];

  const thead = `
    <thead>
      <tr>
        ${columns.map(c => `<th>${c}</th>`).join("")}
      </tr>
    </thead>
  `;

  const tbody = `
    <tbody>
      ${
        rows.map(r => {
          const vals =
            Array.isArray(r)
              ? r
              : Object.values(r);

          return `
            <tr>
              ${
                vals
                  .map(v => `<td>${v}</td>`)
                  .join("")
              }
            </tr>
          `;
        }).join("")
      }
    </tbody>
  `;

  table.innerHTML =
    thead +
    tbody;

  modalOverlay.classList.remove("hidden");
}

function closeModal(){
  modalOverlay.classList.add("hidden");
}

document
  .getElementById("modal-close")
  .addEventListener(
    "click",
    closeModal
  );

modalOverlay.addEventListener(
  "click",
  e => {
    if (e.target === modalOverlay) {
      closeModal();
    }
  }
);

document.addEventListener(
  "keydown",
  e => {
    if (e.key === "Escape") {
      closeModal();
    }
  }
);

/* =========================================================
   SCHEMA VIEW
   ---------------------------------------------------------
   BACKEND CODE PRESERVED.
   ========================================================= */
async function fetchAndRenderSchema() {
  const grid =
    document.getElementById("schema-grid");

  if (!grid || grid.childElementCount > 0) {
    return;
  }

  grid.innerHTML =
    "<p style='color:var(--text-muted);'>Loading schema metadata from Exasol...</p>";

  try {
    const response =
      await fetch(`${API_BASE_URL}/schema`);

    if (!response.ok) {
      throw new Error(
        "Failed to fetch schema."
      );
    }

    const data =
      await response.json();

    const tables =
      data.tables || [];

    grid.innerHTML = "";

    tables.forEach(t => {
      const card =
        document.createElement("div");

      card.className =
        "schema-card";

      const colsHtml =
        t.columns
          .map(col => `
            <div class="schema-col-row">
              <span class="schema-col-name">
                ${col.name || col[0]}
              </span>

              <span class="schema-col-type">
                ${col.type || col[1]}
              </span>
            </div>
          `)
          .join("");

      card.innerHTML = `
        <div class="schema-card-head">

          <div>
            <span class="schema-table-name">
              ${t.table_name || t.table}
            </span>

            <div class="schema-row-count">
              ${t.columns.length} columns
            </div>
          </div>

          <svg
            class="schema-chevron"
            viewBox="0 0 20 20"
            fill="none"
            width="16"
            height="16">

            <path
              d="M5 8l5 5 5-5"
              stroke="currentColor"
              stroke-width="1.8"
              stroke-linecap="round"
              stroke-linejoin="round"/>
          </svg>

        </div>

        <div class="schema-cols">
          ${colsHtml}
        </div>
      `;

      card
        .querySelector(".schema-card-head")
        .addEventListener(
          "click",
          () => card.classList.toggle("open")
        );

      grid.appendChild(card);
    });

  } catch(err) {
    grid.innerHTML = `
      <p style="color:var(--danger)">
        Error loading schema: ${err.message}
      </p>
    `;
  }
}

/* =========================================================
   TEAM
   ========================================================= */
function renderTeam(){
  const grid =
    document.getElementById("team-grid");

  if (!grid) return;

  grid.innerHTML = "";

  mockData.team.forEach(m => {
    const initials =
      m.name
        .split(" ")
        .map(n => n[0])
        .join("");

    const card =
      document.createElement("div");

    card.className =
      "team-card";

    card.innerHTML = `
      <div class="team-avatar">
        ${initials}
      </div>

      <p class="team-name">
        ${m.name}
      </p>

      <p class="team-role">
        ${m.role}
      </p>

      <a
        class="team-linkedin"
        href="${m.linkedin}"
        target="_blank"
        rel="noopener noreferrer"
        aria-label="View ${m.name}'s LinkedIn profile">

        <svg
          viewBox="0 0 24 24"
          width="17"
          height="17"
          fill="currentColor"
          aria-hidden="true">

          <path
            d="M20.45 20.45h-3.56v-5.57c0-1.33-.03-3.04-1.85-3.04-1.85 0-2.14 1.45-2.14 2.95v5.66H9.34V9h3.42v1.56h.05c.48-.9 1.64-1.85 3.37-1.85 3.6 0 4.27 2.37 4.27 5.45v6.29zM5.32 7.43a2.07 2.07 0 110-4.14 2.07 2.07 0 010 4.14zM7.1 20.45H3.54V9H7.1v11.45zM22.23 0H1.77C.79 0 .01.78.01 1.75v20.5c0 .97.78 1.75 1.76 1.75h20.46c.97 0 1.76-.78 1.76-1.75V1.75C23.99.78 23.2 0 22.23 0z"/>
        </svg>

        <span>LinkedIn</span>
      </a>
    `;

    grid.appendChild(card);
  });
}

/* =========================================================
   INIT
   ========================================================= */
removeHistoryView();
removeExasolConnectedPill();
renderTeam();