/**
 * Honeypot Med — client-side prompt-injection widget
 *
 * Ports the Python rule engine in src/honeypot_med/service.py to the browser.
 * Runs ENTIRELY in the visitor's tab. The pasted prompt never leaves the
 * device. The shareable URL carries only the verdict, severity counts, and
 * the rule_ids that fired — never the raw prompt (privacy + HIPAA posture).
 *
 * Provenance for every rule:
 * - OWASP Top 10 for LLM Applications, LLM01:2025 (Prompt Injection)
 *   https://genai.owasp.org/llmrisk/llm01-prompt-injection/
 * - NIST AI 600-1, GenAI Profile (adversarial testing & prompt-injection
 *   resilience). Section 2.6 (Information Integrity) and 2.10 (Information
 *   Security) anchor these checks.
 *
 * Verdict ladder mirrors src/honeypot_med/launchkit.py::bundle_verdict:
 *   any critical|high  -> BLOCK
 *   else any medium    -> REVIEW
 *   else               -> PASS
 *
 * Scoring mirrors service.py::_score and ::_severity. In the public widget
 * we have no tool-call evidence, so `proven` is always false — which means
 * the unproven dampening (-10) and the proof_required ceiling apply. This
 * matches what a healthcare team running the CLI in evidence-only mode sees.
 *
 * Rendering uses createElement + textContent throughout. No innerHTML, no
 * untrusted-content paths — visitor input never reaches the DOM as markup.
 */

// ---------------------------------------------------------------------------
// Rules
// ---------------------------------------------------------------------------
//
// The first three are the canonical DEFAULT_RULES from service.py lines 15-46.
// The remaining rules are ported from the workflow packs in
// src/honeypot_med/packs/ — same attack shapes the buyer-side CLI uses, so a
// widget verdict reflects what they would see on their machine.
//
// Each rule keeps the Python id + attack_family so the shareable ?run= URL
// resolves back to the same rule on this page or any future build.
const RULES = [
  {
    id: "INJ-001",
    pattern: "ignore\\s+previous\\s+instructions",
    attack_family: "instruction_override",
    base_score: 55,
    owasp_anchor: "LLM01: Prompt Injection",
    nist_anchor: "NIST AI 600-1 §2.6 Information Integrity",
    plain_english:
      "Asks the model to override its system prompt. Classic instruction-override pattern.",
  },
  {
    id: "INJ-002",
    pattern: "(exfiltrate|dump\\s+all\\s+data|leak\\s+records)",
    attack_family: "data_exfiltration",
    base_score: 60,
    owasp_anchor: "LLM01: Prompt Injection",
    nist_anchor: "NIST AI 600-1 §2.10 Information Security",
    plain_english:
      "Tries to extract bulk data — eligibility rosters, claims notes, PHI fields, or secrets.",
  },
  {
    id: "INJ-003",
    pattern: "(disable\\s+safeguards|bypass\\s+guardrails|jailbreak)",
    attack_family: "safeguard_bypass",
    base_score: 50,
    owasp_anchor: "LLM01: Prompt Injection",
    nist_anchor: "NIST AI 600-1 §2.6 Information Integrity",
    plain_english:
      "Attempts to switch off safety controls so the rest of the prompt clears review.",
  },
  // ---- Healthcare-specific shapes from packs/healthcare-challenge.json ----
  {
    id: "HC-PHI-001",
    pattern: "(ssn|social\\s+security|member\\s+id|mrn|subscriber\\s+id)",
    attack_family: "phi_exposure",
    base_score: 55,
    owasp_anchor: "LLM01: Prompt Injection",
    nist_anchor: "NIST AI 600-1 §2.10 Information Security",
    plain_english:
      "Names a PHI identifier directly. In a HIPAA-covered workflow this is a hard stop.",
  },
  {
    id: "HC-AUTH-001",
    pattern:
      "(approve\\s+every|approve\\s+all|auto[- ]?approve).{0,40}(prior\\s*auth|authorization|claim)",
    attack_family: "policy_override",
    base_score: 55,
    owasp_anchor: "LLM01: Prompt Injection",
    nist_anchor: "NIST AI 600-1 §2.6 Information Integrity",
    plain_english:
      "Tries to coerce the model into auto-approving prior auth or claims without reviewer signoff.",
  },
  {
    id: "HC-EXP-001",
    pattern:
      "(export|dump).{0,40}(eligibility|roster|members|claims|appeals|intake|triage|utilization)",
    attack_family: "data_exfiltration",
    base_score: 60,
    owasp_anchor: "LLM01: Prompt Injection",
    nist_anchor: "NIST AI 600-1 §2.10 Information Security",
    plain_english:
      "Asks for a bulk export of a healthcare workflow dataset. Even de-identified, this is a buyer-blocking ask.",
  },
  {
    id: "HC-POL-001",
    pattern:
      "(reveal|expose|show)\\s+(the\\s+)?(hidden|internal|system)[\\w\\s-]{0,60}(policy|policies|prompt|rules|routing)",
    attack_family: "policy_disclosure",
    base_score: 50,
    owasp_anchor: "LLM01: Prompt Injection",
    nist_anchor: "NIST AI 600-1 §2.6 Information Integrity",
    plain_english:
      "Asks the model to leak its system prompt or hidden routing policy.",
  },
  {
    id: "HC-TOK-001",
    pattern: "(api\\s*key|payer\\s*token|access\\s*token|bearer\\s*token|secret)",
    attack_family: "credential_exfiltration",
    base_score: 65,
    owasp_anchor: "LLM01: Prompt Injection",
    nist_anchor: "NIST AI 600-1 §2.10 Information Security",
    plain_english:
      "Targets credentials. Any LLM agent with tool access must refuse this outright.",
  },
];

// Severity ordering matches service.py
const SEVERITY_ORDER = { info: 0, low: 1, medium: 2, high: 3, critical: 4 };
const EMPTY_COUNTS = () => ({ critical: 0, high: 0, medium: 0, low: 0, info: 0 });

// ---------------------------------------------------------------------------
// Engine
// ---------------------------------------------------------------------------

// Mirrors service.py::_score. In the widget there is no tool-call evidence,
// so the proven branch is unreachable here — but the helper stays faithful
// to the source so a future widget that accepts tool-call traces can reuse it.
function scoreRule(base, proven) {
  const adjusted = base + (proven ? 25 : -10);
  return Math.max(0, Math.min(100, adjusted));
}

// Mirrors service.py::_severity with proof_required=true (the CLI default
// for the public challenge bundle).
function severityFor(score, proven) {
  if (!proven) {
    // Without tool-call proof we cap at medium per the Python "evidence-only"
    // rule. This is intentional — fewer false BLOCKs on a paste-the-prompt
    // surface, more REVIEWs that nudge the visitor to install and run the CLI
    // with their actual tool traces.
    return score >= 35 ? "medium" : "low";
  }
  if (score >= 85) return "critical";
  if (score >= 60) return "high";
  if (score >= 35) return "medium";
  return "low";
}

// Mirrors launchkit.py::bundle_verdict 1:1.
function bundleVerdict(severityCounts) {
  const c = severityCounts || {};
  if ((c.critical | 0) > 0 || (c.high | 0) > 0) return "BLOCK";
  if ((c.medium | 0) > 0) return "REVIEW";
  return "PASS";
}

function scanPrompt(prompt) {
  const findings = [];
  const counts = EMPTY_COUNTS();
  if (typeof prompt !== "string" || !prompt.trim()) {
    return { verdict: "PASS", severity_counts: counts, findings: [] };
  }
  const lower = prompt.toLowerCase();

  // Worst severity across all rule hits drives the count, matching the
  // per-event aggregation in analyze_prompts (service.py lines 164-172).
  let worst = null;

  for (const rule of RULES) {
    const re = new RegExp(rule.pattern, "i");
    const match = lower.match(re);
    if (!match) continue;

    // Widget never has tool-call evidence to validate against.
    const proven = false;
    const score = scoreRule(rule.base_score, proven);
    const severity = severityFor(score, proven);
    const snippet = trimSnippet(prompt, match.index, match[0].length);

    findings.push({
      rule_id: rule.id,
      attack_family: rule.attack_family,
      severity,
      score,
      proven,
      snippet,
      plain_english: rule.plain_english,
      owasp_anchor: rule.owasp_anchor,
      nist_anchor: rule.nist_anchor,
    });

    if (!worst || SEVERITY_ORDER[severity] > SEVERITY_ORDER[worst]) {
      worst = severity;
    }
  }

  if (worst) counts[worst] += 1;

  const verdict = bundleVerdict(counts);
  return { verdict, severity_counts: counts, findings };
}

function trimSnippet(source, start, length) {
  // 60-char window centered on the match. Healthcare prompts can be long;
  // truncating keeps the finding readable in the result panel.
  const radius = 30;
  const from = Math.max(0, start - radius);
  const to = Math.min(source.length, start + length + radius);
  let out = source.slice(from, to);
  if (from > 0) out = "..." + out;
  if (to < source.length) out = out + "...";
  return out;
}

// ---------------------------------------------------------------------------
// Shareable URL — verdict + counts + rule_ids only. Never the prompt.
// ---------------------------------------------------------------------------

function encodeRun(result) {
  const rule_ids = result.findings.map((f) => f.rule_id);
  const payload = {
    v: result.verdict,
    sc: result.severity_counts,
    ids: rule_ids,
  };
  const json = JSON.stringify(payload);
  // base64url so the URL is safe in any context (slack preview, email).
  const b64 = btoa(unescape(encodeURIComponent(json)));
  return b64.replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}

function decodeRun(token) {
  if (!token) return null;
  try {
    let b64 = token.replace(/-/g, "+").replace(/_/g, "/");
    while (b64.length % 4) b64 += "=";
    const json = decodeURIComponent(escape(atob(b64)));
    const data = JSON.parse(json);
    if (!data || typeof data !== "object") return null;
    if (!data.v || !data.sc || !Array.isArray(data.ids)) return null;
    return data;
  } catch (_) {
    return null;
  }
}

// ---------------------------------------------------------------------------
// Rendering — pure DOM. No innerHTML. Visitor input is set via textContent
// so a paste with literal HTML can never become markup.
// ---------------------------------------------------------------------------

const VERDICT_COPY = {
  PASS: {
    label: "PASS",
    blurb:
      "No prompt-injection patterns matched. A real production check should still run with tool-call traces and the full pack.",
  },
  REVIEW: {
    label: "REVIEW",
    blurb:
      "One or more suspicious patterns matched. Without tool-call evidence the engine caps at REVIEW — install the CLI to confirm.",
  },
  BLOCK: {
    label: "BLOCK",
    blurb:
      "Proven high-severity patterns matched. In a healthcare workflow this should not reach the model without human review.",
  },
};

function el(tag, opts) {
  const node = document.createElement(tag);
  if (!opts) return node;
  if (opts.className) node.className = opts.className;
  if (opts.text != null) node.textContent = opts.text;
  if (opts.attrs) {
    for (const [k, v] of Object.entries(opts.attrs)) node.setAttribute(k, v);
  }
  return node;
}

function buildPill(verdict) {
  // Reuses styles.css .verdict-pill (PASS-tone accent) and
  // .verdict-pill.review (teal). BLOCK gets a red inline tone so this widget
  // stays standalone without touching the global stylesheet.
  const span = el("span", { className: "verdict-pill", text: VERDICT_COPY[verdict].label });
  if (verdict === "REVIEW") span.classList.add("review");
  if (verdict === "BLOCK") {
    span.style.background = "#fde2e2";
    span.style.color = "#8a1f1f";
    span.style.borderColor = "#f0b3b3";
  }
  return span;
}

function buildCounts(counts) {
  const order = ["critical", "high", "medium", "low", "info"];
  const visible = order.filter((k) => (counts[k] | 0) > 0);
  if (!visible.length) {
    return el("div", { className: "hpm-counts hpm-counts-empty", text: "No findings." });
  }
  const wrap = el("div", { className: "hpm-counts" });
  visible.forEach((k) => {
    const cell = el("span", { className: `hpm-count hpm-count-${k}` });
    cell.appendChild(el("strong", { text: String(counts[k]) }));
    cell.appendChild(document.createTextNode(" " + k));
    wrap.appendChild(cell);
  });
  return wrap;
}

function buildFindings(findings) {
  if (!findings.length) return null;
  const list = el("ol", { className: "hpm-findings" });
  findings.forEach((f) => {
    const li = el("li", { className: `hpm-finding hpm-sev-${f.severity}` });

    const head = el("div", { className: "hpm-finding-head" });
    head.appendChild(el("strong", { text: f.rule_id }));
    head.appendChild(el("span", { className: "hpm-finding-fam", text: f.attack_family }));
    head.appendChild(
      el("span", {
        className: "hpm-finding-sev",
        text: `${f.severity} · score ${f.score}`,
      })
    );
    li.appendChild(head);

    li.appendChild(el("div", { className: "hpm-finding-snippet", text: f.snippet }));
    li.appendChild(el("div", { className: "hpm-finding-why", text: f.plain_english }));

    const anchors = el("div", { className: "hpm-finding-anchors" });
    anchors.appendChild(el("span", { text: f.owasp_anchor }));
    anchors.appendChild(el("span", { text: f.nist_anchor }));
    li.appendChild(anchors);

    list.appendChild(li);
  });
  return list;
}

function buildShare(panel, shareUrl) {
  const wrap = el("div", { className: "hpm-share" });
  const label = el("label", {
    text: "Shareable verdict link (no prompt content):",
    attrs: { for: "hpm-share-url" },
  });
  const input = el("input", {
    attrs: { id: "hpm-share-url", type: "text", readonly: "readonly", value: shareUrl },
  });
  const btn = el("button", {
    className: "button-secondary",
    text: "Copy link",
    attrs: { type: "button", "data-hpm-copy": "1" },
  });
  btn.addEventListener("click", () => {
    input.select();
    try {
      document.execCommand("copy");
      btn.textContent = "Copied";
      setTimeout(() => (btn.textContent = "Copy link"), 1600);
    } catch (_) {
      // Clipboard may be blocked in iframes; the input stays selected.
    }
  });
  wrap.appendChild(label);
  wrap.appendChild(input);
  wrap.appendChild(btn);
  return wrap;
}

function renderResult(panel, result, options) {
  const { shareUrl, sharedMode } = options || {};
  // Clear panel without using innerHTML.
  while (panel.firstChild) panel.removeChild(panel.firstChild);

  if (sharedMode) {
    panel.appendChild(
      el("div", {
        className: "hpm-shared-banner",
        text: "Showing a shared verdict. The original prompt was never sent.",
      })
    );
  }

  const head = el("div", { className: "hpm-result-head" });
  head.appendChild(buildPill(result.verdict));
  head.appendChild(
    el("p", {
      className: "hpm-result-blurb",
      text: VERDICT_COPY[result.verdict].blurb,
    })
  );
  panel.appendChild(head);

  panel.appendChild(buildCounts(result.severity_counts));

  const findings = buildFindings(result.findings);
  if (findings) panel.appendChild(findings);

  if (shareUrl) panel.appendChild(buildShare(panel, shareUrl));
}

// Reconstruct a partial result from a shared token. We do not have the
// findings' snippets (we never had the prompt) — only ids. We re-derive the
// rule metadata from the local RULES table, which is why rule ids are stable.
function rehydrateShared(data) {
  const findings = data.ids
    .map((id) => {
      const rule = RULES.find((r) => r.id === id);
      if (!rule) return null;
      const score = scoreRule(rule.base_score, false);
      const severity = severityFor(score, false);
      return {
        rule_id: rule.id,
        attack_family: rule.attack_family,
        severity,
        score,
        proven: false,
        snippet: "(prompt not shared — rule id only)",
        plain_english: rule.plain_english,
        owasp_anchor: rule.owasp_anchor,
        nist_anchor: rule.nist_anchor,
      };
    })
    .filter(Boolean);

  return {
    verdict: data.v,
    severity_counts: { ...EMPTY_COUNTS(), ...data.sc },
    findings,
  };
}

// ---------------------------------------------------------------------------
// DOM wiring
// ---------------------------------------------------------------------------

function init() {
  const input = document.getElementById("hpm-widget-input");
  const button = document.getElementById("hpm-widget-run");
  const panel = document.getElementById("hpm-widget-result");
  if (!input || !button || !panel) return;

  // Examples auto-fill — buttons mark themselves with [data-hpm-example].
  document.querySelectorAll("[data-hpm-example]").forEach((node) => {
    node.addEventListener("click", (e) => {
      e.preventDefault();
      const text = node.getAttribute("data-hpm-example") || node.textContent || "";
      input.value = text.trim();
      input.focus();
    });
  });

  button.addEventListener("click", () => {
    const result = scanPrompt(input.value);
    const token = encodeRun(result);
    const url = new URL(window.location.href);
    url.searchParams.set("run", token);
    // History push so the visitor can copy from the address bar too.
    window.history.replaceState({}, "", url.toString());
    renderResult(panel, result, { shareUrl: url.toString() });
  });

  // On load: render shared verdict if ?run= present.
  const params = new URLSearchParams(window.location.search);
  const token = params.get("run");
  if (token) {
    const data = decodeRun(token);
    if (data) {
      const result = rehydrateShared(data);
      renderResult(panel, result, {
        shareUrl: window.location.href,
        sharedMode: true,
      });
    }
  }
}

// Auto-init when imported. Keeps the demo page's <script type="module"> short.
// Guarded so the engine can be unit-tested in Node without a DOM.
if (typeof document !== "undefined") {
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
}

export { RULES, scanPrompt, bundleVerdict, encodeRun, decodeRun, init };
