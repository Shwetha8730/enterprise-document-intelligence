const API = "";

const state = {
    documents: [],
    activeDocId: null,
    docCache: {},
};

// ---------------------------------------------------------------- utils

function $(sel) { return document.querySelector(sel); }
function $all(sel) { return Array.from(document.querySelectorAll(sel)); }

function toast(msg) {
    const el = $("#toast");
    el.textContent = msg;
    el.classList.add("show");
    setTimeout(() => el.classList.remove("show"), 2600);
}

function fmtPct(v) { return `${(v * 100).toFixed(1)}%`; }

function titleCase(key) {
    return key.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

async function api(path, opts = {}) {
    const res = await fetch(API + path, opts);
    if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.detail || `Request failed (${res.status})`);
    }
    const ct = res.headers.get("content-type") || "";
    return ct.includes("application/json") ? res.json() : res;
}

// ---------------------------------------------------------------- nav

$all("#nav-segment button").forEach((btn) => {
    btn.addEventListener("click", () => switchView(btn.dataset.view));
});

function switchView(view) {
    $all("#nav-segment button").forEach((b) => b.classList.toggle("active", b.dataset.view === view));
    $all(".view").forEach((v) => v.classList.remove("active"));
    $(`#view-${view}`).classList.add("active");
    if (view === "audit") loadAuditLog();
    if (view === "analytics") loadAnalytics();
}

// ---------------------------------------------------------------- meta / hero

async function loadMeta() {
    try {
        const meta = await api("/api/meta");
        $("#mode-pill-text").textContent = meta.embedding_mode;
        $("#hero-doc-count").textContent = meta.processed_count;
        $("#hero-mode").textContent = meta.is_sentence_transformers ? "ST" : "TF-IDF";
    } catch (e) {
        $("#mode-pill-text").textContent = "offline";
    }
}

// ---------------------------------------------------------------- upload

const dropzone = $("#dropzone");
const fileInput = $("#file-input");

dropzone.addEventListener("click", () => fileInput.click());
dropzone.addEventListener("dragover", (e) => { e.preventDefault(); dropzone.classList.add("dragover"); });
dropzone.addEventListener("dragleave", () => dropzone.classList.remove("dragover"));
dropzone.addEventListener("drop", (e) => {
    e.preventDefault();
    dropzone.classList.remove("dragover");
    handleFiles(e.dataTransfer.files);
});
fileInput.addEventListener("change", () => handleFiles(fileInput.files));

async function handleFiles(fileList) {
    for (const file of Array.from(fileList)) {
        dropzone.querySelector(".title").innerHTML = `<span class="spinner" style="display:inline-block; vertical-align:-3px; margin-right:8px;"></span>Processing ${file.name}…`;
        try {
            const form = new FormData();
            form.append("file", file);
            const data = await api("/api/upload", { method: "POST", body: form });

            if (data.already_processed) {
                toast(`${data.filename} has already been processed.`);
            } else {
                toast(`Processed: ${data.filename}`);
            }

            await refreshDocList();
            await selectDocument(data.doc_id);
        } catch (e) {
            toast(`Failed to process ${file.name}: ${e.message}`);
        }
    }
    dropzone.querySelector(".title").textContent = "Drop files here or click to browse";
    fileInput.value = "";
}

async function refreshDocList() {
    const data = await api("/api/documents");
    state.documents = data.documents;
    renderDocList();
    loadMeta();
}

function renderDocList() {
    const list = $("#doc-list");
    list.innerHTML = "";
    if (!state.documents.length) {
        $("#upload-empty").style.display = "block";
        return;
    }
    $("#upload-empty").style.display = "none";

    state.documents.forEach((doc) => {
        const chip = document.createElement("div");
        chip.className = "doc-chip" + (doc.doc_id === state.activeDocId ? " active" : "");
        chip.innerHTML = `
        <span class="fname">${doc.filename}</span>
        <button class="delete-btn"
            data-id="${doc.doc_id}"
            title="Delete">
        🗑
    </button>`;
        chip.addEventListener("click", (e) => {
            if (e.target.classList.contains("delete-btn"))
              return;
            selectDocument(doc.doc_id);
            });
        list.appendChild(chip);
        chip.querySelector(".delete-btn").onclick = async (e) => {
            e.stopPropagation();
            if (!confirm(`Delete "${doc.filename}" ?`))
               return;
            try {
               await api(`/api/documents/${doc.doc_id}`, {
                   method: "DELETE"
                });
                toast("Document deleted");
                delete state.docCache[doc.doc_id];
                if (state.activeDocId === doc.doc_id) {
                    state.activeDocId = null;
                    $("#doc-detail").style.display = "none";
              }
                await refreshDocList();

                if ($("#view-analytics").classList.contains("active")) {
                    loadAnalytics();
                }
             }
             catch(err){
                 toast(err.message);
             }
         };
    });
}

async function selectDocument(docId) {
    state.activeDocId = docId;
    renderDocList();

    let doc = state.docCache[docId];
    if (!doc) {
        doc = await api(`/api/documents/${docId}`);
        state.docCache[docId] = doc;
    }
    renderDocDetail(doc);
}

function renderDocDetail(doc) {
    try {
        const result = doc.result;
    $("#doc-detail").style.display = "block";

    const cls = result.classification;
    $("#pred-type").textContent = cls.predicted_type.toUpperCase();
    $("#pred-confidence").textContent = fmtPct(cls.confidence) + " confidence";

    const scores = Object.entries(cls.all_scores).sort((a, b) => b[1] - a[1]);
    const maxScore = scores.length ? scores[0][1] : 1;
    $("#score-bars").innerHTML = scores.map(([label, val], i) => `
        <div class="bar-row">
            <span class="bar-label">${label}</span>
            <span class="bar-track"><span class="bar-fill${i === 0 ? " top" : ""}" style="width:${(val / maxScore) * 100}%"></span></span>
            <span class="bar-val">${fmtPct(val)}</span>
        </div>
    `).join("");

    const comp = result.completeness_check;
    $("#completeness-badge").innerHTML = comp.is_complete
        ? `<span class="badge badge-success">Complete</span>`
        : `<span class="badge badge-warning">Needs review</span>`;
    $("#completeness-text").textContent = comp.recommendation;

    const metaEntries = Object.entries(result.metadata).filter(([k, v]) => v && k !== "missing_fields");
    $("#metadata-list").innerHTML = metaEntries.length
        ? metaEntries.map(([k, v]) => `
            <div class="kv-row">
                <span class="k">${titleCase(k)}</span>
                <span class="v">${Array.isArray(v) ? v.join(", ") : v}</span>
            </div>
        `).join("")
        : `<p style="color:var(--text-muted); font-size:13px; margin:0;">No metadata extracted for this document.</p>`;

    $("#doc-summary").textContent = result.summary;
    $("#raw-text").textContent = doc.text;

    $("#download-original").onclick = () => window.open(`/api/documents/${doc.doc_id}/file`, "_blank");
    $("#download-report").onclick = () => window.open(`/api/documents/${doc.doc_id}/report`, "_blank");

    $("#answer-box").style.display = "none";
    $("#question-input").value = "";
    $("#ask-btn").onclick = () => askQuestion(doc.doc_id);
    $("#question-input").onkeydown = (e) => { if (e.key === "Enter") askQuestion(doc.doc_id); };

    } catch (err) {
        console.error("Failed to render document details:", err);
    }
}
async function askQuestion(docId) {
    const question = $("#question-input").value.trim();
    if (!question) return;
    $("#ask-btn").disabled = true;
    try {
        const answer = await api(`/api/documents/${docId}/ask`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ question }),
        });
        $("#answer-box").style.display = "block";
        $("#answer-text").textContent = answer.answer;
        $("#answer-meta").textContent = `Confidence: ${answer.confidence} · Agent: ${answer.agent}`;
    } catch (e) {
        toast(`Couldn't answer that: ${e.message}`);
    } finally {
        $("#ask-btn").disabled = false;
    }
}

// ---------------------------------------------------------------- search

let searchTimer = null;
$("#search-input").addEventListener("input", (e) => {
    clearTimeout(searchTimer);
    const q = e.target.value.trim();
    if (!q) {
        $("#search-results").innerHTML = "";
        $("#search-empty").style.display = "block";
        return;
    }
    searchTimer = setTimeout(() => runSearch(q), 350);
});

async function runSearch(q) {
    $("#search-empty").style.display = "none";
    try {
        const data = await api(`/api/search?q=${encodeURIComponent(q)}`);
        if (!data.results.length) {
            $("#search-results").innerHTML = `<p style="color:var(--text-muted); font-size:13.5px;">No matching documents found.</p>`;
            return;
        }
        $("#search-results").innerHTML = data.results.map((r) => `
            <div class="result-card">
                <div class="rhead">
                    <h4>${r.filename}</h4>
                    <span class="badge badge-accent">${r.doc_type.toUpperCase()}</span>
                </div>
                <p style="margin:0; font-size:12.5px; color:var(--text-muted); font-family:var(--font-mono);">${(r.score*100).toFixed(1)}% Match</p>
                ${r.snippet ? `<div class="snippet">${r.snippet}</div>` : ""}
            </div>
        `).join("");
    } catch (e) {
        $("#search-results").innerHTML = `<p style="color:var(--danger); font-size:13.5px;">${e.message}</p>`;
    }
}

// ---------------------------------------------------------------- audit log

async function loadAuditLog() {
    const stream = $("#log-stream");
    stream.innerHTML = `<div style="padding:20px; color:var(--text-muted); font-size:13px;">Loading…</div>`;
    try {
        const data = await api("/api/audit-log?limit=200");
        if (!data.logs.length) {
            stream.innerHTML = `<div class="empty-state"><div class="icon">🧾</div><div class="title">No actions logged yet</div><div class="sub">Process a document to populate the audit trail.</div></div>`;
            return;
        }
        stream.innerHTML = data.logs.map((log) => `
            <div class="log-row">
                <span class="lg-id">#${log.id}</span>
                <span class="lg-doc">${log.doc_id}</span>
                <span class="lg-action">${log.action}</span>
                <span class="lg-detail" title="${(log.details || "").replace(/"/g, "&quot;")}">${log.details || ""}</span>
                <span class="lg-time">${(log.timestamp || "").replace("T", " ").split(".")[0]}</span>
            </div>
        `).join("");
    } catch (e) {
        stream.innerHTML = `<div style="padding:20px; color:var(--danger); font-size:13px;">${e.message}</div>`;
    }
}

// ---------------------------------------------------------------- analytics

let charts = {};

function destroyChart(key) {
    if (charts[key]) { charts[key].destroy(); delete charts[key]; }
}

const CHART_FONT = { family: "IBM Plex Mono", size: 11 };
const AXIS_COLOR = "#5C6B82";
const GRID_COLOR = "rgba(255,255,255,0.05)";

async function loadAnalytics() {
    try {
        const stats = await api("/api/stats");

        const counts = stats.document_types || {};
        $("#type-stat-row").innerHTML = 
        Object.entries(counts).map(([type,count])=>`
            <div class="stat-card">
                <div class="label">${type}</div>
                <div class="value">${count}</div>
            </div>
        `).join("");

        if (typeof Chart === "undefined") {
          console.error("Chart.js failed to load.");
          toast("Chart.js not loaded");
          return;
    }

        destroyChart("dist");
        const canvas = $("#chart-distribution");

        charts.dist = new Chart(canvas.getContext("2d"), {
            type: "bar",
            data: {
                labels: Object.keys(counts),
                datasets: [{ data: Object.values(counts), backgroundColor: "#F2A93B", borderRadius: 4, maxBarThickness: 34 }],
            },
            options: baseChartOptions(false),
        });

        destroyChart("conf");
        const confData = stats.confidence_by_type_percent || {};
        charts.conf = new Chart($("#chart-confidence").getContext("2d"), {
            type: "bar",
            data: {
                labels: Object.keys(confData),
                datasets: [{ data: Object.values(confData), backgroundColor: "#35D0A3", borderRadius: 4, maxBarThickness: 34 }],
            },
            options: baseChartOptions(false),
        });

        $("#upload-count").textContent =
        stats.documents_processed;
    } catch (e) {
        toast(`Couldn't load analytics: ${e.message}`);
    }
}

function baseChartOptions(showLegendGrid) {
    return {
        responsive: true,
        plugins: { legend: { display: false } },
        scales: {
            x: { ticks: { color: AXIS_COLOR, font: CHART_FONT }, grid: { color: "transparent" } },
            y: { ticks: { color: AXIS_COLOR, font: CHART_FONT }, grid: { color: GRID_COLOR }, beginAtZero: true },
        },
    };
}

// ---------------------------------------------------------------- init

async function initializeApp() {
    try {
        await api("/api/reset-session", {
            method: "POST"
        });
    } catch (e) {
    toast("Unable to reset previous session.");
}

    await loadMeta();
    await refreshDocList();
}

initializeApp();