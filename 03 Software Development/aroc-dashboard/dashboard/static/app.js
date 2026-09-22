/* AROC Dashboard frontend — GPLv3.  Renders the generic card model from /api/status. */
(() => {
  "use strict";

  const ICONS = {
    dns: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3c3 3.5 3 14.5 0 18M12 3c-3 3.5-3 14.5 0 18"/></svg>',
    shield: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 3l8 3v6c0 5-3.5 8-8 9-4.5-1-8-4-8-9V6z"/><path d="M9 12l2 2 4-4"/></svg>',
    clock: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/></svg>',
    firewall: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="4" width="18" height="16" rx="2"/><path d="M3 10h18M3 15h18M9 10v5M15 4v6M12 15v5"/></svg>',
    switch: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="8" width="20" height="8" rx="2"/><path d="M6 12h.01M10 12h.01M14 12h.01M18 12h.01"/></svg>',
    server: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="18" height="7" rx="2"/><rect x="3" y="14" width="18" height="7" rx="2"/><path d="M7 6.5h.01M7 17.5h.01"/></svg>',
    play: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="9"/><path d="M10 8l6 4-6 4z"/></svg>',
    chip: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="6" y="6" width="12" height="12" rx="2"/><path d="M9 2v4M15 2v4M9 18v4M15 18v4M2 9h4M2 15h4M18 9h4M18 15h4"/></svg>',
    link: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10 14a4 4 0 005.7 0l3-3a4 4 0 00-5.7-5.7l-1 1"/><path d="M14 10a4 4 0 00-5.7 0l-3 3a4 4 0 005.7 5.7l1-1"/></svg>',
    generic: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="4" y="4" width="16" height="16" rx="3"/><path d="M8 12h8M12 8v8"/></svg>',
  };

  const $ = (sel, el = document) => el.querySelector(sel);
  const grid = $("#grid");
  const tpl = $("#card-tpl");
  const cards = new Map();  // id -> element
  let refreshMs = 30000;
  let timer = null;

  const fmtTime = (unix) => unix ? new Date(unix * 1000).toLocaleTimeString() : "—";
  const ago = (unix) => {
    if (!unix) return "never";
    const s = Math.max(0, Math.round(Date.now() / 1000 - unix));
    return s < 60 ? `${s}s ago` : s < 3600 ? `${Math.floor(s / 60)}m ago` : `${Math.floor(s / 3600)}h ago`;
  };
  const isNum = (v) => typeof v === "number" || (typeof v === "string" && /^[\d.,%]+(\s?(Mbps|Kbps|W|°C|%))?$/.test(v.trim()));

  function sparkline(container, history) {
    container.innerHTML = "";
    const spark = document.createElement("div");
    spark.className = "spark";
    const data = (history || []).slice(-40);
    if (data.length === 0) { spark.classList.add("empty"); }
    const max = Math.max(1e-9, ...data);
    const n = Math.max(data.length, 12);
    for (let i = 0; i < n; i++) {
      const bar = document.createElement("span");
      const v = data[i];
      if (v === undefined) { bar.style.height = "8%"; bar.style.background = "var(--line)"; }
      else {
        bar.style.height = `${Math.max(8, (v / max) * 100)}%`;
        bar.title = Number.isInteger(v) ? v.toLocaleString() : v.toFixed(2);
        if (i === data.length - 1) bar.classList.add("last");
      }
      spark.appendChild(bar);
    }
    container.appendChild(spark);
  }

  function render(svc) {
    let el = cards.get(svc.id);
    if (!el) {
      el = tpl.content.firstElementChild.cloneNode(true);
      el.dataset.id = svc.id;
      cards.set(svc.id, el);
      grid.appendChild(el);
      el.addEventListener("click", (ev) => {
        if (ev.target.closest(".card-head")) manualRefresh(svc.id);
      });
    }
    el.classList.toggle("wide", !!svc.wide);
    el.classList.toggle("errored", !!svc.error);

    $(".card-icon", el).innerHTML = ICONS[svc.icon] || ICONS.generic;
    $(".card-title", el).textContent = svc.title;
    const status = $(".status", el);
    status.className = `status ${svc.status.level}`;
    $(".dot", status).className = `dot ${svc.status.level}`;
    $(".status-label", el).textContent = svc.status.label;
    $(".card-desc", el).textContent = svc.description || "";

    const body = $(".card-body", el);
    const hero = $(".hero", el);
    if (svc.hero) {
      body.classList.remove("no-hero");
      hero.hidden = false;
      hero.innerHTML = `<div class="hero-value"></div><div class="hero-label"></div><div class="hero-spark"></div>`;
      $(".hero-value", hero).textContent = svc.hero.value ?? "—";
      $(".hero-label", hero).textContent = svc.hero.label ?? "";
      sparkline($(".hero-spark", hero), svc.hero.history);
    } else {
      body.classList.add("no-hero");
      hero.hidden = true;
    }

    const stats = $(".stats", el);
    stats.innerHTML = "";
    for (const s of svc.stats || []) {
      const d = document.createElement("div");
      d.className = `stat ${s.level || ""}`;
      const value = document.createElement("div");
      value.className = "stat-value";
      value.append(document.createTextNode(s.value ?? "—"));
      if (s.sub) {
        const sub = document.createElement("span");
        sub.className = `stat-sub ${s.level || ""}`;
        sub.textContent = s.sub;
        value.appendChild(sub);
      }
      const label = document.createElement("div");
      label.className = "stat-label";
      label.textContent = s.label;
      d.append(value, label);
      stats.appendChild(d);
    }

    const tables = $(".tables", el);
    tables.innerHTML = "";
    for (const t of svc.tables || []) {
      const wrap = document.createElement("div");
      wrap.className = "tbl";
      const title = document.createElement("div");
      title.className = "tbl-title";
      title.textContent = t.title;
      const table = document.createElement("table");
      const thead = table.createTHead().insertRow();
      t.columns.forEach((c, i) => {
        const th = document.createElement("th");
        th.textContent = c;
        if (i > 0 && t.rows.every((r) => isNum(r[i]))) th.className = "num";
        thead.appendChild(th);
      });
      const tbody = table.createTBody();
      t.rows.forEach((row, ri) => {
        const tr = tbody.insertRow();
        row.forEach((cell, ci) => {
          const td = tr.insertCell();
          if (ci === 0 && t.levels) {
            const dot = document.createElement("span");
            dot.className = `dot ${t.levels[ri] || "unknown"}`;
            td.appendChild(dot);
          }
          td.append(document.createTextNode(String(cell ?? "")));
          if (ci > 0 && isNum(cell)) td.className = "num";
        });
      });
      wrap.append(title, table);
      tables.appendChild(wrap);
    }

    const items = $(".items", el);
    items.innerHTML = "";
    for (const it of svc.items || []) {
      const span = document.createElement("span");
      span.className = "item";
      if (it.title) span.title = it.title;
      const dot = document.createElement("span");
      dot.className = `dot ${it.level || "unknown"}`;
      span.append(dot, document.createTextNode(it.label));
      items.appendChild(span);
    }

    const err = $(".card-error", el);
    err.hidden = !svc.error;
    err.textContent = svc.error || "";

    const btn = $(".btn", el);
    if (svc.url) { btn.hidden = false; btn.href = svc.url; } else { btn.hidden = true; }

    const stale = svc.updated && (Date.now() / 1000 - svc.updated) > Math.max(svc.interval || 30, refreshMs / 1000) * 3;
    $(".card-foot", el).innerHTML =
      `<span>${svc.type}</span><span class="${stale ? "stale" : ""}">updated ${ago(svc.updated)}${stale ? " • stale" : ""}</span>`;
  }

  async function load() {
    try {
      const r = await fetch("/api/status", { cache: "no-store" });
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      const data = await r.json();
      document.title = data.title;
      $("#title").textContent = data.title;
      $("#subtitle").textContent = data.subtitle || "";
      refreshMs = (data.refresh_seconds || 30) * 1000;
      const ok = data.services.filter((s) => !s.error).length;
      $("#summary").textContent = `${ok}/${data.services.length} services ok`;
      $("#footer-right").textContent = `v${data.version} • polled ${fmtTime(data.server_time)}`;
      if (data.services.length === 0) {
        grid.innerHTML = `<div class="placeholder">No services configured — add some to config.yaml.</div>`;
      }
      const seen = new Set();
      for (const svc of data.services) { render(svc); seen.add(svc.id); }
      for (const [id, el] of cards) if (!seen.has(id)) { el.remove(); cards.delete(id); }
    } catch (e) {
      $("#summary").textContent = `dashboard unreachable: ${e.message}`;
    } finally {
      clearTimeout(timer);
      timer = setTimeout(load, refreshMs);
    }
  }

  async function manualRefresh(id) {
    try {
      const r = await fetch(`/api/services/${encodeURIComponent(id)}/refresh`, { method: "POST" });
      if (r.ok) render(await r.json());
    } catch (_) { /* ignore; next poll will show state */ }
  }

  $("#refresh-all").addEventListener("click", () => load());
  setInterval(() => { $("#clock").textContent = new Date().toLocaleString(); }, 1000);
  document.addEventListener("visibilitychange", () => { if (!document.hidden) load(); });
  load();
})();
