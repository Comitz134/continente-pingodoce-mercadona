"use strict";

/* ================= Utilidades ================= */

const $ = (sel) => document.querySelector(sel);

const DIAS = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"];
const STORAGE_KEY = "prato-da-semana:v1";
const PRICE_MAX_HARD = 6; // topo do slider = "6 € ou mais"

function esc(s) {
  return String(s ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function norm(s) {
  return String(s ?? "")
    .toLowerCase()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "");
}

function shuffle(arr) {
  const a = arr.slice();
  for (let i = a.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [a[i], a[j]] = [a[j], a[i]];
  }
  return a;
}

function money(v) {
  return v.toLocaleString("pt-PT", {
    style: "currency",
    currency: "EUR",
    minimumFractionDigits: 2,
  });
}

const PLACEHOLDER =
  "data:image/svg+xml," +
  encodeURIComponent(
    '<svg xmlns="http://www.w3.org/2000/svg" width="600" height="400">' +
      '<rect width="600" height="400" fill="#eef1ee"/>' +
      '<circle cx="300" cy="200" r="70" fill="#ffffff" stroke="#cbd5d1" stroke-width="6"/>' +
      '<circle cx="300" cy="200" r="26" fill="#d1d5db"/>' +
      '<text x="300" y="352" text-anchor="middle" font-family="sans-serif" font-size="26" fill="#9ca3af">Sem foto</text>' +
      "</svg>"
  );

let toastTimer = null;
function toast(msg) {
  const el = $("#toast");
  el.textContent = msg;
  el.hidden = false;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => (el.hidden = true), 2200);
}

/* ================= Estado ================= */

const state = {
  priceMin: 0.5,
  priceMax: PRICE_MAX_HARD,
  allergies: new Set(),
  avoid: [],
  stores: new Set(["continente", "pingoDoce", "mercadona"]),
  planIds: null, // null = ainda não gerado
  cart: [],
};

function loadState() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return;
    const saved = JSON.parse(raw);
    if (saved && typeof saved === "object") {
      if (typeof saved.priceMin === "number") state.priceMin = saved.priceMin;
      if (typeof saved.priceMax === "number") state.priceMax = saved.priceMax;
      if (Array.isArray(saved.allergies)) state.allergies = new Set(saved.allergies);
      if (Array.isArray(saved.avoid)) state.avoid = saved.avoid;
      if (Array.isArray(saved.stores) && saved.stores.length)
        state.stores = new Set(saved.stores);
      if (Array.isArray(saved.planIds)) state.planIds = saved.planIds;
      if (Array.isArray(saved.cart)) state.cart = saved.cart;
    }
  } catch (e) {
    /* ignore */
  }
}

function saveState() {
  try {
    localStorage.setItem(
      STORAGE_KEY,
      JSON.stringify({
        priceMin: state.priceMin,
        priceMax: state.priceMax,
        allergies: [...state.allergies],
        avoid: state.avoid,
        stores: [...state.stores],
        planIds: state.planIds,
        cart: state.cart,
      })
    );
  } catch (e) {
    /* ignore */
  }
}

/* ================= Filtragem ================= */

function matchesFilters(r) {
  // Orçamento
  const inBudget = r.preco >= state.priceMin && (state.priceMax >= PRICE_MAX_HARD || r.preco <= state.priceMax);
  if (!inBudget) return false;

  // Alergias
  for (const a of state.allergies) {
    if (r.alergenios.includes(a)) return false;
  }

  // Alimentos a evitar (procura em ingredientes e no nome)
  if (state.avoid.length) {
    const nomeTodo = norm(r.nome + " " + r.nomeOrig + " " + r.categoria);
    const ingredientes = r.ingredientes.map((i) => norm(i.nome)).join(" ");
    for (const termo of state.avoid) {
      const t = norm(termo);
      if (!t) continue;
      if (nomeTodo.includes(t) || ingredientes.includes(t)) return false;
    }
  }

  // Supermercados
  if (!r.lojas.some((l) => state.stores.has(l))) return false;

  return true;
}

function pool() {
  return window.RECIPES.filter(matchesFilters);
}

/* ================= Seleção semanal ================= */

function pickWeek(poolArr, n = 7) {
  const shuffled = shuffle(poolArr);
  const result = [];
  const used = new Set();
  for (let i = 0; i < n; i++) {
    const recentCats = new Set(result.slice(-2).map((r) => r.categoria));
    let chosen = shuffled.find((r) => !used.has(r.id) && !recentCats.has(r.categoria));
    if (!chosen) chosen = shuffled.find((r) => !used.has(r.id));
    if (!chosen) break;
    used.add(chosen.id);
    result.push(chosen);
  }
  return result;
}

function resolvePlan(ids) {
  const byId = new Map(window.RECIPES.map((r) => [r.id, r]));
  return ids.map((id) => byId.get(id)).filter(Boolean);
}

/* ================= Carrinho ================= */

const UNIT_LABELS = { kg: "kg", l: "L", un: "un.", colher: "c.", "maço": "maço", lata: "lata" };

function parseQtd(texto) {
  const t = norm(String(texto)).trim();
  if (!t || t === "q.b." || t === "qb") return { n: 1, un: "colher" };
  const frac = t.match(/^(\d+)\s*\/\s*(\d+)\s*(.*)$/);
  let n = 0;
  let resto = t;
  if (frac) {
    n = parseFloat(frac[1]) / parseFloat(frac[2]);
    resto = frac[3].trim();
  } else {
    const num = t.match(/^(\d+(?:[.,]\d+)?)\s*(.*)$/);
    if (num) {
      n = parseFloat(num[1].replace(",", "."));
      resto = num[2].trim();
    }
  }
  if (/^(g|gramas?)$/.test(resto)) return { n, un: "g" };
  if (/^(kg|quilos?)$/.test(resto)) return { n, un: "kg" };
  if (/^(ml|mililitros?)$/.test(resto)) return { n, un: "ml" };
  if (/^(l|litros?)$/.test(resto)) return { n, un: "l" };
  if (/c\.\s*sopa|colher/.test(resto)) return { n, un: "colher" };
  if (/c\.\s*ch[aá]/.test(resto)) return { n: n * 0.33, un: "colher" };
  if (/pitada/.test(resto)) return { n: n * 0.2, un: "colher" };
  if (/ma[cç]o/.test(resto)) return { n, un: "maço" };
  if (/lata/.test(resto)) return { n, un: "lata" };
  if (/dente/.test(resto)) return { n, un: "un" };
  if (/folha|bolbo|rolo|placa|posta|unidade|un/.test(resto)) return { n, un: "un" };
  return { n: n || 1, un: "un" };
}

function converter(n, de, para, entry) {
  if (de === para) return n;
  if (para === "kg" && de === "g") return n / 1000;
  if (para === "g" && de === "kg") return n * 1000;
  if (para === "l" && de === "ml") return n / 1000;
  if (para === "ml" && de === "l") return n * 1000;
  if (para === "l" && de === "colher") return n * 0.015;
  if (para === "colher" && de === "ml") return n / 15;
  if (para === "kg" && de === "colher") return n * 0.008;
  if (para === "kg" && de === "un" && entry && entry.unKg) return n * entry.unKg;
  return n;
}

function precarLinha(nome, qtd) {
  const key = norm(nome);
  const entry = window.PRECOS[key];
  const parsed = parseQtd(qtd);
  if (entry) {
    const n = converter(parsed.n, parsed.un, entry.u, entry);
    return { key, nome, n, unit: entry.u, preco: { c: entry.c, p: entry.p, m: entry.m } };
  }
  const fb = window.PRECOS_FALLBACK[parsed.un] || window.PRECOS_FALLBACK.un;
  return { key, nome, n: parsed.n, unit: parsed.un, preco: { c: fb.c, p: fb.p, m: fb.m } };
}

function arredonda(v) {
  return Math.round(v * 100) / 100;
}

function formatQty(n, unit) {
  if (unit === "kg") return n >= 1 ? `${arredonda(n)} kg` : `${Math.round(n * 1000)} g`;
  if (unit === "l") return n >= 1 ? `${arredonda(n)} L` : `${Math.round(n * 1000)} ml`;
  return `${arredonda(n)} ${UNIT_LABELS[unit] || unit}`;
}

/* Preços reais (Supabase) — com fallback para os preços curados. */

const SUPABASE_ON = () =>
  !!(window.SUPABASE && window.SUPABASE.url && window.SUPABASE.anonKey);

const STORE_ID_MAP = {
  continente: "continente",
  pingo_doce: "pingoDoce",
  mercadona: "mercadona",
  mercadona_es: "mercadona",
  mercadona_pt: "mercadona",
};

async function precosReais(nome) {
  if (!SUPABASE_ON()) return null;
  try {
    const url =
      `${window.SUPABASE.url}/rest/v1/products` +
      `?select=name,price,price_per_unit,unit,store,url` +
      `&name=ilike.*${encodeURIComponent(norm(nome))}*&order=price.asc&limit=50`;
    const r = await fetch(url, {
      headers: {
        apikey: window.SUPABASE.anonKey,
        Authorization: `Bearer ${window.SUPABASE.anonKey}`,
      },
    });
    if (!r.ok) return null;
    const rows = await r.json();
    const best = { continente: null, pingoDoce: null, mercadona: null };
    for (const row of rows) {
      const s = STORE_ID_MAP[row.store];
      if (s && row.price != null && best[s] == null) {
        best[s] = { nome: row.name, preco: Number(row.price), url: row.url };
      }
    }
    return Object.values(best).some(Boolean) ? best : null;
  } catch (e) {
    return null;
  }
}

async function enriquecerLinha(linha) {
  const real = await precosReais(linha.nome);
  if (real) linha.real = real;
  return linha;
}

function addToCart(linha) {
  const existente = state.cart.find((i) => i.key === linha.key && i.unit === linha.unit);
  if (existente) {
    existente.n += linha.n;
    if (linha.real && !existente.real) existente.real = linha.real;
  } else {
    state.cart.push({
      key: linha.key, nome: linha.nome, n: linha.n, unit: linha.unit,
      preco: linha.preco, real: linha.real || null,
    });
  }
  saveState();
  updateCartBadge();
  renderCart();
}

async function addRecipeToCart(r) {
  for (const i of r.ingredientes) {
    addToCart(await enriquecerLinha(precarLinha(i.nome, i.qtd)));
  }
  toast(`🛒 ${r.nome} adicionado`);
}

function removeFromCart(key) {
  state.cart = state.cart.filter((i) => i.key !== key);
  saveState();
  updateCartBadge();
  renderCart();
}

function cartTotals() {
  const t = { continente: 0, pingoDoce: 0, mercadona: 0 };
  state.cart.forEach((i) => {
    t.continente += i.real && i.real.continente ? i.real.continente.preco : i.n * i.preco.c;
    t.pingoDoce  += i.real && i.real.pingoDoce  ? i.real.pingoDoce.preco  : i.n * i.preco.p;
    t.mercadona  += i.real && i.real.mercadona  ? i.real.mercadona.preco  : i.n * i.preco.m;
  });
  return t;
}

function updateCartBadge() {
  const count = state.cart.length;
  const badge = $("#cart-badge");
  badge.hidden = count === 0;
  badge.textContent = count;
}

function renderCart() {
  const totals = cartTotals();
  const cheapest = Math.min(totals.continente, totals.pingoDoce, totals.mercadona);

  $("#cart-stores").innerHTML = window.STORES.map((s) => {
    const val = totals[s.id];
    const winner = Math.abs(val - cheapest) < 0.005;
    return `<div class="store-total${winner ? " winner" : ""}">
      <span class="dot" style="background:${esc(s.cor)}"></span>
      <span class="nome">${esc(s.label)}</span>
      ${winner ? '<span class="trophy">🏆</span>' : ""}
      <span class="valor">${money(val)}</span>
    </div>`;
  }).join("");

  const wrap = $("#cart-items");
  if (!state.cart.length) {
    wrap.innerHTML = `<div class="cart-empty">O carrinho está vazio.<br/>Abre a ementa e toca em <strong>🛒 Adicionar à lista</strong> (ou em <strong>＋</strong> num ingrediente).</div>`;
  } else {
    wrap.innerHTML = state.cart
      .map((i) => {
        const val = (loja) => (i.real && i.real[loja] ? i.real[loja].preco : i.n * i.preco[loja]);
        const best = Math.min(val("continente"), val("pingoDoce"), val("mercadona"));
        const chip = (loja) => {
          const s = window.STORES.find((x) => x.id === loja);
          const r = i.real && i.real[loja];
          const v = r ? r.preco : i.n * i.preco[loja];
          const bestHere = Math.abs(v - best) < 0.005;
          const titulo = r ? esc(r.nome) : esc(s.label);
          const link = r && r.url ? ` href="${esc(r.url)}" target="_blank" rel="noopener"` : "";
          return `<a class="price-chip${bestHere ? " best" : ""}" style="background:${esc(s.cor)}"${link}>${titulo} ${money(v)}</a>`;
        };
        const realTag = i.real ? '<span class="real-tag">preço real</span>' : "";
        return `<div class="cart-item">
          <div class="cart-item-top">
            <span class="inome">${esc(i.nome)}</span>
            <span class="iqtd">${esc(formatQty(i.n, i.unit))} ${realTag}</span>
            <button class="rm" type="button" data-cart-remove="${esc(i.key)}" aria-label="Remover ${esc(i.nome)}">✕</button>
          </div>
          <div class="cart-item-prices">
            ${chip("continente")}
            ${chip("pingoDoce")}
            ${chip("mercadona")}
          </div>
        </div>`;
      })
      .join("");
  }
  updateCartBadge();
}

/* ================= Config UI ================= */

function buildAllergenChips() {
  const wrap = $("#allergen-chips");
  wrap.innerHTML = "";
  for (const a of window.ALLERGENS) {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "chip";
    btn.setAttribute("type", "button");
    btn.setAttribute("aria-pressed", String(state.allergies.has(a.id)));
    btn.innerHTML = `${esc(a.emoji)} ${esc(a.label)}`;
    btn.addEventListener("click", () => {
      if (state.allergies.has(a.id)) state.allergies.delete(a.id);
      else state.allergies.add(a.id);
      btn.setAttribute("aria-pressed", String(state.allergies.has(a.id)));
      saveState();
    });
    wrap.appendChild(btn);
  }
}

function buildStoreToggles() {
  const wrap = $("#store-toggles");
  wrap.innerHTML = "";
  for (const s of window.STORES) {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "store-toggle";
    btn.setAttribute("type", "button");
    btn.setAttribute("aria-pressed", String(state.stores.has(s.id)));
    btn.innerHTML =
      `<span class="store-logo" style="background:${esc(s.cor)}">${esc(s.label.slice(0, 2).toUpperCase())}</span>` +
      `<span class="store-name">${esc(s.label)}</span>` +
      `<span class="store-check">✓</span>`;
    btn.addEventListener("click", () => {
      if (state.stores.has(s.id)) state.stores.delete(s.id);
      else state.stores.add(s.id);
      btn.setAttribute("aria-pressed", String(state.stores.has(s.id)));
      saveState();
    });
    wrap.appendChild(btn);
  }
}

function renderAvoidChips() {
  const wrap = $("#avoid-chips");
  wrap.innerHTML = "";
  for (const termo of state.avoid) {
    const chip = document.createElement("button");
    chip.type = "button";
    chip.className = "chip";
    chip.innerHTML = `${esc(termo)} <span class="x">✕</span>`;
    chip.addEventListener("click", () => {
      state.avoid = state.avoid.filter((t) => t !== termo);
      saveState();
      renderAvoidChips();
    });
    wrap.appendChild(chip);
  }
}

function addAvoid(termo) {
  const t = termo.trim();
  if (!t) return;
  if (state.avoid.some((x) => norm(x) === norm(t))) return;
  state.avoid.push(t);
  saveState();
  renderAvoidChips();
}

function updatePriceUI() {
  const min = state.priceMin;
  const max = state.priceMax;
  $("#price-min").value = min;
  $("#price-max").value = max;
  $("#price-min-label").textContent = money(min);
  $("#price-max-label").textContent = max >= PRICE_MAX_HARD ? "6 €+" : money(max);

  const minPct = ((min - 0.5) / (PRICE_MAX_HARD - 0.5)) * 100;
  const maxPct = ((max - 0.5) / (PRICE_MAX_HARD - 0.5)) * 100;
  const track = document.querySelector(".dual-range-track");
  track.style.left = minPct + "%";
  track.style.right = 100 - maxPct + "%";

  $("#price-hint").textContent =
    max >= PRICE_MAX_HARD
      ? `Receitas entre ${money(min)} e ${money(PRICE_MAX_HARD)} (ou mais) por dose`
      : `Receitas entre ${money(min)} e ${money(max)} por dose`;
}

function bindPrice() {
  const minEl = $("#price-min");
  const maxEl = $("#price-max");

  minEl.addEventListener("input", () => {
    let v = parseFloat(minEl.value);
    if (v > state.priceMax) {
      state.priceMax = v;
      maxEl.value = v;
    }
    state.priceMin = v;
    saveState();
    updatePriceUI();
  });

  maxEl.addEventListener("input", () => {
    let v = parseFloat(maxEl.value);
    if (v < state.priceMin) {
      state.priceMin = v;
      minEl.value = v;
    }
    state.priceMax = v;
    saveState();
    updatePriceUI();
  });
}

/* ================= Navegação ================= */

function show(viewId) {
  $("#view-config").hidden = viewId !== "config";
  $("#view-plan").hidden = viewId !== "plan";
  $("#view-cart").hidden = viewId !== "cart";
  $("#btn-back").hidden = viewId === "config";
  $("#btn-cart-fab").hidden = viewId !== "plan";
  window.scrollTo({ top: 0 });
}

/* ================= Plano (resultados) ================= */

function badgeLoja(id) {
  const s = window.STORES.find((x) => x.id === id);
  if (!s) return "";
  return `<span class="badge" style="background:${esc(s.cor)}">${esc(s.label)}</span>`;
}

function cardHTML(r, diaIndex) {
  const algs = r.alergenios.length
    ? r.alergenios
        .map((id) => {
          const a = window.ALLERGENS.find((x) => x.id === id);
          return `<span class="badge alg">${a ? esc(a.emoji + " " + a.label) : esc(id)}</span>`;
        })
        .join("")
    : `<span class="badge clean">✓ Sem alergénios comuns</span>`;

  const ing = r.ingredientes
    .map(
      (i) =>
        `<li><span class="in">${esc(i.nome)}</span><span class="q">${esc(i.qtd)}</span>` +
        `<button class="add-ing" type="button" data-action="add-ing" data-nome="${esc(i.nome)}" data-qtd="${esc(i.qtd)}" aria-label="Adicionar ${esc(i.nome)}">＋</button></li>`
    )
    .join("");

  return `
    <article class="day-card" data-id="${esc(r.id)}">
      <div class="day-head">
        <div class="day-name">${esc(DIAS[diaIndex])}
          <span class="cat">${esc(r.categoria)} · ${esc(r.nomeOrig)}</span>
        </div>
      </div>
      <img class="day-photo" src="${esc(r.foto)}" alt="${esc(r.nome)}" loading="lazy"
           referrerpolicy="no-referrer" onerror="this.onerror=null;this.src=PLACEHOLDER" />
      <div class="day-body">
        <h3 class="day-title">${esc(r.nome)}</h3>
        <p class="day-sub">Estima-se ${money(r.preco)} por dose</p>
        <div class="meta">
          <span class="badge price">${money(r.preco)} / dose</span>
          <span class="badge time">⏱ ${r.tempo} min</span>
          ${algs}
        </div>
        <div class="store-badges">
          ${r.lojas.map(badgeLoja).join("")}
        </div>
        <p class="dica"><strong>💡 Dica:</strong> ${esc(r.dica)}</p>
        <details class="ingredientes">
          <summary>🧾 Lista de compras (${r.ingredientes.length})</summary>
          <ul class="ing-list">${ing}</ul>
        </details>
        <div class="day-actions">
          <button class="btn btn-swap" type="button" data-action="swap">🔁 Trocar</button>
          <button class="btn btn-primary" type="button" data-action="add-all">🛒 Adicionar à lista</button>
        </div>
      </div>
    </article>`;
}

function renderPlan() {
  const current = resolvePlan(state.planIds || []);
  const available = pool();

  const summary = $("#plan-summary");
  summary.innerHTML = `
    <div>
      <div class="num">${available.length}</div>
      <div class="lbl">receitas dentro dos teus filtros</div>
    </div>
    <div style="text-align:right">
      <div class="num">${money(current.reduce((s, r) => s + r.preco, 0))}</div>
      <div class="lbl">custo estimado da semana</div>
    </div>`;

  const wrap = $("#plan-days");
  if (!current.length) {
    wrap.innerHTML = `<div class="empty">
        <p style="font-size:2rem">🤷</p>
        <p><strong>Sem receitas suficientes.</strong><br/>
        Alarga o orçamento ou remove algumas alergias/alimentos a evitar.</p>
      </div>`;
    return;
  }

  wrap.innerHTML = current.map((r, i) => cardHTML(r, i)).join("");
}

function swapRecipe(diaIndex) {
  const current = resolvePlan(state.planIds || []);
  const usedIds = new Set(current.map((r) => r.id));
  const available = pool().filter((r) => !usedIds.has(r.id));
  if (!available.length) {
    toast("Não há mais receitas dentro dos teus filtros");
    return;
  }
  const diaCategoria = current[diaIndex].categoria;
  const preferidos = available.filter((r) => r.categoria !== diaCategoria);
  const novo = (preferidos.length ? preferidos : available)[0];
  const ids = current.map((r) => r.id);
  ids[diaIndex] = novo.id;
  state.planIds = ids;
  saveState();
  renderPlan();
  toast(`Trocaste para: ${novo.nome}`);
}

function generatePlan() {
  if (!state.stores.size) {
    $("#config-error").textContent = "Escolhe pelo menos um supermercado.";
    $("#config-error").hidden = false;
    toast("Escolhe pelo menos um supermercado");
    return;
  }
  $("#config-error").hidden = true;

  const available = pool();
  if (!available.length) {
    $("#config-error").textContent =
      "Nenhuma receita corresponde aos teus filtros. Tenta alargar o orçamento ou remover restrições.";
    $("#config-error").hidden = false;
    return;
  }

  state.planIds = pickWeek(available, 7).map((r) => r.id);
  saveState();
  renderPlan();
  show("plan");
  toast(`Ementa gerada (${state.planIds.length} dias)`);
}

/* ================= PWA ================= */

let deferredPrompt = null;

function setupPWA() {
  if ("serviceWorker" in navigator && location.protocol.startsWith("http")) {
    window.addEventListener("load", () => {
      navigator.serviceWorker.register("sw.js").catch(() => {});
    });
  }

  const standalone =
    window.matchMedia("(display-mode: standalone)").matches || navigator.standalone === true;

  window.addEventListener("beforeinstallprompt", (e) => {
    e.preventDefault();
    deferredPrompt = e;
    if (!standalone) $("#btn-install").hidden = false;
  });

  $("#btn-install").addEventListener("click", async () => {
    if (!deferredPrompt) return;
    deferredPrompt.prompt();
    await deferredPrompt.userChoice;
    deferredPrompt = null;
    $("#btn-install").hidden = true;
  });

  window.addEventListener("appinstalled", () => {
    $("#btn-install").hidden = true;
    toast("App instalada 🎉");
  });
}

/* ================= Init ================= */

function init() {
  loadState();
  buildAllergenChips();
  buildStoreToggles();
  renderAvoidChips();
  bindPrice();
  updatePriceUI();
  setupPWA();

  $("#btn-add-avoid").addEventListener("click", () => {
    addAvoid($("#avoid-input").value);
    $("#avoid-input").value = "";
    $("#avoid-input").focus();
  });
  $("#avoid-input").addEventListener("keydown", (e) => {
    if (e.key === "Enter") {
      e.preventDefault();
      addAvoid($("#avoid-input").value);
      $("#avoid-input").value = "";
    }
  });

  $("#btn-generate").addEventListener("click", generatePlan);
  $("#btn-regenerate").addEventListener("click", generatePlan);
  $("#btn-edit").addEventListener("click", () => show("config"));
  $("#btn-back").addEventListener("click", () => {
    show($("#view-cart").hidden ? "config" : "plan");
  });

  $("#plan-days").addEventListener("click", (e) => {
    const btn = e.target.closest("[data-action]");
    if (!btn) return;
    const card = btn.closest(".day-card");
    const cards = [...document.querySelectorAll(".day-card")];
    const idx = cards.indexOf(card);
    if (btn.dataset.action === "swap") {
      swapRecipe(idx);
    } else if (btn.dataset.action === "add-all") {
      const r = resolvePlan(state.planIds || [])[idx];
      if (r) addRecipeToCart(r);
    } else if (btn.dataset.action === "add-ing") {
      (async () => {
        addToCart(await enriquecerLinha(precarLinha(btn.dataset.nome, btn.dataset.qtd)));
        toast("Adicionado à lista");
      })();
    }
  });

  $("#cart-items").addEventListener("click", (e) => {
    const rm = e.target.closest("[data-cart-remove]");
    if (rm) removeFromCart(rm.dataset.cartRemove);
  });
  $("#btn-cart-clear").addEventListener("click", () => {
    state.cart = [];
    saveState();
    updateCartBadge();
    renderCart();
    toast("Lista limpa");
  });
  $("#btn-cart-fab").addEventListener("click", () => {
    renderCart();
    show("cart");
  });
  $("#btn-cart-back").addEventListener("click", () => show("plan"));

  updateCartBadge();

  // Mostra o plano guardado, se existir; caso contrário a configuração.
  if (state.planIds && state.planIds.length) {
    renderPlan();
    show("plan");
  } else {
    show("config");
  }
}

document.addEventListener("DOMContentLoaded", init);
