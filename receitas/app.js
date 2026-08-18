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
  favorites: [],
  savedPlans: [],
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
      if (Array.isArray(saved.favorites)) state.favorites = saved.favorites;
      if (Array.isArray(saved.savedPlans)) state.savedPlans = saved.savedPlans;
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
        favorites: state.favorites,
        savedPlans: state.savedPlans,
      })
    );
  } catch (e) {
    /* ignore */
  }
  pushCloud();
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
      const t = norm(termo).trim();
      if (!t) continue;
      // Aceita singular/plural (ex.: "cogumelo" ≈ "cogumelos").
      const variantes = new Set([t, t.replace(/s$/, ""), t + "s"]);
      if ([...variantes].some((v) => nomeTodo.includes(v) || ingredientes.includes(v))) return false;
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
  const termo = norm(nome).trim();
  if (!termo) return null;

  const select = "name,price,price_per_unit,unit,store,url";
  const pick = (rows) => {
    const best = { continente: null, pingoDoce: null, mercadona: null };
    for (const row of rows) {
      const s = STORE_ID_MAP[row.store];
      if (s && row.price != null && best[s] == null) {
        best[s] = { nome: row.name, preco: Number(row.price), url: row.url };
      }
    }
    return Object.values(best).some(Boolean) ? best : null;
  };
  const fetchRows = async (filter) => {
    const url =
      `${window.SUPABASE.url}/rest/v1/products?select=${select}` +
      `&name=${filter}&order=price.asc&limit=60`;
    const r = await fetch(url, {
      headers: {
        apikey: window.SUPABASE.anonKey,
        Authorization: `Bearer ${window.SUPABASE.anonKey}`,
      },
    });
    if (!r.ok) return null;
    return r.json();
  };

  try {
    // 1) Prefere produtos que COMEÇAM pelo ingrediente (ex.: "Azeite Virgem…").
    const exactos = await fetchRows(`ilike.${encodeURIComponent(termo)}*`);
    const direto = exactos ? pick(exactos) : null;
    if (direto) return direto;
    // 2) Senão, cai para "contém" (ex.: "Sardinha em Azeite").
    const contidos = await fetchRows(`ilike.*${encodeURIComponent(termo)}*`);
    return contidos ? pick(contidos) : null;
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
  const badge = $("#nav-cart-badge");
  if (!badge) return;
  badge.hidden = count === 0;
  badge.textContent = count;
}

function renderCart() {
  const totals = cartTotals();
  const cheapest = Math.min(totals.continente, totals.pingoDoce, totals.mercadona);

  const hasItems = state.cart.length > 0;
  $("#cart-stores").innerHTML = window.STORES.map((s) => {
    const val = totals[s.id];
    const winner = hasItems && Math.abs(val - cheapest) < 0.005;
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

/* ================= Conta / sincronização ================= */

let authFormMode = null; // null | "signup" | "login"
let isGate = false;
let currentView = "config";
let lastMainView = "config";

const SYNC_KEYS = ["preferences", "plan", "cart", "favorites", "plans"];

function preferencesSnapshot() {
  return {
    priceMin: state.priceMin,
    priceMax: state.priceMax,
    allergies: [...state.allergies],
    avoid: state.avoid,
    stores: [...state.stores],
  };
}

function applyPreferences(p) {
  if (!p) return;
  if (typeof p.priceMin === "number") state.priceMin = p.priceMin;
  if (typeof p.priceMax === "number") state.priceMax = p.priceMax;
  if (Array.isArray(p.allergies)) state.allergies = new Set(p.allergies);
  if (Array.isArray(p.avoid)) state.avoid = p.avoid;
  if (Array.isArray(p.stores) && p.stores.length) state.stores = new Set(p.stores);
}

function applyCloud(data) {
  if (!data) return;
  if (data.preferences) applyPreferences(data.preferences);
  if ("plan" in data) state.planIds = data.plan;
  if (Array.isArray(data.cart)) state.cart = data.cart;
  if (Array.isArray(data.favorites)) state.favorites = data.favorites;
  if (Array.isArray(data.plans)) state.savedPlans = data.plans;
  saveState();
}

function refreshAllUI() {
  buildAllergenChips();
  buildStoreToggles();
  buildAvoidChips();
  updatePriceUI();
  renderPlan();
  renderCart();
  renderFavorites();
  updateFavButtons();
  renderSavedPlans();
  updateCartBadge();
  renderAccountUI();
}

let syncTimer = null;
function pushCloud() {
  if (!window.Auth || !window.Auth.isLoggedIn()) return;
  clearTimeout(syncTimer);
  syncTimer = setTimeout(() => {
    window.Auth.setData("preferences", preferencesSnapshot());
    window.Auth.setData("plan", state.planIds);
    window.Auth.setData("cart", state.cart);
    window.Auth.setData("favorites", state.favorites);
    window.Auth.setData("plans", state.savedPlans);
  }, 400);
}

async function onSignedIn() {
  const data = await window.Auth.getAllData();
  const hasCloud = SYNC_KEYS.some((k) => k in data);
  if (hasCloud) {
    applyCloud(data);
    refreshAllUI();
    toast("Conta ligada — dados carregados");
  } else {
    await window.Auth.setData("preferences", preferencesSnapshot());
    await window.Auth.setData("plan", state.planIds);
    await window.Auth.setData("cart", state.cart);
    await window.Auth.setData("favorites", state.favorites);
    await window.Auth.setData("plans", state.savedPlans);
    toast("Conta ligada — dados guardados");
  }
}

function continueAsGuest() {
  window.Auth.setMode("guest");
  authFormMode = null;
  isGate = false;
  renderAccountUI();
  const target = state.planIds && state.planIds.length ? "plan" : "config";
  show(target);
  toast("Modo convidado — dados guardados neste aparelho");
}

function renderAccountUI() {
  const logged = window.Auth.isLoggedIn();
  $("#account-guest").hidden = logged || authFormMode !== null;
  $("#account-forms").hidden = logged || authFormMode === null;
  $("#account-logged").hidden = !logged;
  if (logged) {
    $("#account-email").textContent = window.Auth.email() || "";
  }
  renderSavedPlans();
  $("#btn-account").classList.toggle("is-on", logged);
}

function renderAuthForm() {
  const isSignup = authFormMode === "signup";
  $("#account-form-title").innerHTML = isSignup
    ? 'Criar <span class="script">conta</span>'
    : 'Entrar <span class="script">na conta</span>';
  $("#btn-auth-submit").textContent = isSignup ? "Criar conta" : "Entrar";
  $("#auth-password").setAttribute("autocomplete", isSignup ? "new-password" : "current-password");
  const msg = $("#auth-msg");
  msg.textContent = "";
  msg.className = "hint";
}

async function handleAuthSubmit() {
  const emailVal = $("#auth-email").value.trim();
  const pass = $("#auth-password").value;
  const msg = $("#auth-msg");
  msg.className = "hint";
  if (!emailVal || !pass) {
    msg.textContent = "Preenche o email e a password.";
    msg.className = "error";
    return;
  }
  if (pass.length < 6) {
    msg.textContent = "A password tem de ter pelo menos 6 caracteres.";
    msg.className = "error";
    return;
  }
  $("#btn-auth-submit").disabled = true;
  const res =
    authFormMode === "signup"
      ? await window.Auth.signUp(emailVal, pass)
      : await window.Auth.signIn(emailVal, pass);
  $("#btn-auth-submit").disabled = false;

  if (res.ok && res.needsConfirm) {
    msg.textContent =
      "Enviamos um email de confirmação. Confirma e depois toca em «Já tenho conta» para entrar.";
    msg.className = "hint";
    authFormMode = null;
    renderAccountUI();
    return;
  }
  if (!res.ok) {
    msg.textContent = res.error || "Não foi possível. Tenta novamente.";
    msg.className = "error";
    return;
  }

  $("#auth-email").value = "";
  $("#auth-password").value = "";
  authFormMode = null;
  window.Auth.setMode("account");
  isGate = false;
  await onSignedIn();
  renderAccountUI();
  let target = lastMainView || "config";
  if (target === "plan" && (!state.planIds || !state.planIds.length)) target = "config";
  show(target);
}

/* ================= Guardados (favoritos + ementas) ================= */

function toggleFavorite(id) {
  const idx = state.favorites.indexOf(id);
  if (idx >= 0) state.favorites.splice(idx, 1);
  else state.favorites.push(id);
  saveState();
  updateFavButtons();
  renderFavorites();
  toast(state.favorites.includes(id) ? "⭐ Guardado" : "Removido dos guardados");
}

function updateFavButtons() {
  document.querySelectorAll(".day-fav").forEach((btn) => {
    const card = btn.closest(".day-card");
    const fav = card ? state.favorites.includes(card.dataset.id) : false;
    btn.setAttribute("aria-pressed", String(fav));
    btn.setAttribute("aria-label", fav ? "Remover dos guardados" : "Guardar receita");
    btn.textContent = fav ? "★" : "☆";
  });
}

function renderFavorites() {
  const wrap = $("#favorites-list");
  if (!wrap) return;
  const recipes = state.favorites
    .map((id) => window.RECIPES.find((r) => r.id === id))
    .filter(Boolean);
  if (!recipes.length) {
    wrap.innerHTML = `<div class="empty"><p class="big">⭐</p>Não tens receitas guardadas.<br/>Toca na estrela de uma receita para a guardar.</div>`;
    return;
  }
  wrap.innerHTML = recipes.map((r) => favoriteCardHTML(r)).join("");
  observeReveals();
}

function saveCurrentPlan() {
  const ids = state.planIds || [];
  if (!ids.length) {
    toast("Gera primeiro uma ementa");
    return;
  }
  const now = new Date();
  const nome = `Ementa ${String(now.getDate()).padStart(2, "0")}/${String(now.getMonth() + 1).padStart(2, "0")}`;
  state.savedPlans.push({
    id: "p" + now.getTime(),
    nome,
    criadoEm: now.toISOString(),
    recipeIds: ids.slice(),
  });
  saveState();
  renderSavedPlans();
  toast("Ementa guardada 💾");
}

function loadSavedPlan(id) {
  const p = state.savedPlans.find((x) => x.id === id);
  if (!p || !Array.isArray(p.recipeIds) || !p.recipeIds.length) return;
  state.planIds = p.recipeIds.slice();
  saveState();
  renderPlan();
  show("plan");
  toast(`Ementa carregada: ${p.nome}`);
}

function deleteSavedPlan(id) {
  state.savedPlans = state.savedPlans.filter((x) => x.id !== id);
  saveState();
  renderSavedPlans();
}

function renderSavedPlans() {
  const wrap = $("#account-plans");
  if (!wrap) return;
  if (!state.savedPlans.length) {
    wrap.innerHTML = `<div class="cart-empty">Sem ementas guardadas.<br/>Na ementa, toca em <strong>💾 Guardar</strong>.</div>`;
    return;
  }
  wrap.innerHTML = state.savedPlans
    .map((p) => {
      const d = p.criadoEm ? new Date(p.criadoEm) : null;
      const data = d
        ? `${String(d.getDate()).padStart(2, "0")}/${String(d.getMonth() + 1).padStart(2, "0")}/${d.getFullYear()}`
        : "";
      return `<div class="plan-item">
        <div class="plan-item-info">
          <div class="plan-item-name">${esc(p.nome)}</div>
          <div class="plan-item-meta">${esc(data)} · ${p.recipeIds.length} receitas</div>
        </div>
        <div class="plan-item-actions">
          <button class="btn btn-ghost btn-sm" type="button" data-plan-load="${esc(p.id)}">Carregar</button>
          <button class="btn btn-sm plan-del" type="button" data-plan-del="${esc(p.id)}" aria-label="Apagar ${esc(p.nome)}">✕</button>
        </div>
      </div>`;
    })
    .join("");
}

function handleRecipeAction(e) {
  const btn = e.target.closest("[data-action]");
  if (!btn) return;
  const card = btn.closest(".day-card");
  const rid = card ? card.dataset.id : null;
  const r = rid ? window.RECIPES.find((x) => x.id === rid) : null;
  const action = btn.dataset.action;

  if (action === "swap") {
    const cards = [...document.querySelectorAll("#plan-days .day-card")];
    swapRecipe(cards.indexOf(card));
  } else if (action === "fav") {
    if (r) toggleFavorite(r.id);
  } else if (action === "add-all") {
    if (r) addRecipeToCart(r);
  } else if (action === "add-ing") {
    if (r) {
      (async () => {
        addToCart(await enriquecerLinha(precarLinha(btn.dataset.nome, btn.dataset.qtd)));
        toast("Adicionado à lista");
      })();
    }
  }
}

/* ================= Receitas (browse por método) ================= */

let methodFilter = "todos"; // todos | airfryer | microondas | forno_fogao

function buildMethodChips() {
  const wrap = $("#method-chips");
  const opts = [
    { id: "todos", label: "Todos", emoji: "🍽️" },
    { id: "airfryer", label: "Airfryer", emoji: "🌪️" },
    { id: "microondas", label: "Microondas", emoji: "⚡" },
    { id: "forno_fogao", label: "Forno/Fogão", emoji: "🔥" },
  ];
  wrap.innerHTML = "";
  for (const o of opts) {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "chip";
    btn.setAttribute("type", "button");
    btn.setAttribute("aria-pressed", String(methodFilter === o.id));
    btn.innerHTML = `${o.emoji} ${esc(o.label)}`;
    btn.addEventListener("click", () => {
      methodFilter = o.id;
      buildMethodChips();
      renderReceitas();
    });
    wrap.appendChild(btn);
  }
}

function methodMatches(r) {
  const m = window.METODOS[r.id] || "fogao";
  if (methodFilter === "todos") return true;
  if (methodFilter === "airfryer") return m === "airfryer";
  if (methodFilter === "microondas") return m === "microondas";
  if (methodFilter === "forno_fogao") return m === "forno" || m === "fogao";
  return true;
}

function renderReceitas() {
  const lista = window.RECIPES.filter(methodMatches);
  $("#receitas-count").textContent = `${lista.length} receita${lista.length === 1 ? "" : "s"}`;
  const wrap = $("#receitas-list");
  if (!lista.length) {
    wrap.innerHTML = `<div class="empty"><p class="big">🍳</p>Sem receitas para este método.</div>`;
    return;
  }
  wrap.innerHTML = lista.map((r) => browseCardHTML(r)).join("");
  observeReveals();
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
    btn.setAttribute("aria-label", s.label);
    btn.innerHTML =
      `<span class="store-logo"><img src="${esc(s.logo)}" alt="" /></span>` +
      `<span class="store-check" aria-hidden="true">✓</span>`;
    btn.addEventListener("click", () => {
      if (state.stores.has(s.id)) state.stores.delete(s.id);
      else state.stores.add(s.id);
      btn.setAttribute("aria-pressed", String(state.stores.has(s.id)));
      saveState();
    });
    wrap.appendChild(btn);
  }
}

function toggleAvoid(termo) {
  const t = termo.trim();
  if (!t) return;
  const idx = state.avoid.findIndex((x) => norm(x) === norm(t));
  if (idx >= 0) state.avoid.splice(idx, 1);
  else state.avoid.push(t);
  saveState();
  buildAvoidChips();
  renderFoodList();
}

function buildAvoidChips() {
  const wrap = $("#avoid-chips");
  wrap.innerHTML = "";
  for (const termo of window.AVOID_PRESETS) {
    const active = state.avoid.some((x) => norm(x) === norm(termo));
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "chip";
    btn.setAttribute("type", "button");
    btn.setAttribute("aria-pressed", String(active));
    btn.textContent = termo;
    btn.addEventListener("click", () => toggleAvoid(termo));
    wrap.appendChild(btn);
  }
}

function renderFoodList() {
  const input = $("#food-search-input");
  const termo = input ? norm(input.value).trim() : "";
  const lista = termo
    ? window.AVOIDABLE_FOODS.filter((f) => norm(f).includes(termo))
    : window.AVOIDABLE_FOODS;

  const wrap = $("#food-list");
  if (wrap) {
    wrap.innerHTML = "";
    for (const f of lista) {
      const active = state.avoid.some((x) => norm(x) === norm(f));
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "chip";
      btn.setAttribute("type", "button");
      btn.setAttribute("aria-pressed", String(active));
      btn.textContent = f;
      btn.addEventListener("click", () => toggleAvoid(f));
      wrap.appendChild(btn);
    }
  }

  const count = $("#food-count");
  if (count) {
    count.textContent = lista.length
      ? `${lista.length} alimento${lista.length === 1 ? "" : "s"} · ${state.avoid.length} selecionado${state.avoid.length === 1 ? "" : "s"}`
      : "Sem resultados. Tenta outra palavra.";
  }
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

function homeView() {
  return state.planIds && state.planIds.length ? "plan" : "config";
}

function activeTabFor(viewId) {
  if (viewId === "config" || viewId === "plan") return "home";
  if (viewId === "receitas" || viewId === "favorites") return "receitas";
  if (viewId === "cart" || viewId === "foods") return "ingredientes";
  return "conta";
}

function show(viewId) {
  ["config", "plan", "cart", "foods", "account", "favorites", "receitas"].forEach((v) => {
    $("#view-" + v).hidden = v !== viewId;
  });
  currentView = viewId;
  if (viewId === "plan" || viewId === "config") lastMainView = viewId;
  const showBack = (viewId === "foods" || viewId === "favorites") && !isGate;
  $("#btn-back").hidden = !showBack;
  $("#btn-settings").hidden = isGate;
  $("#tabbar").hidden = isGate;
  document.querySelectorAll(".tab").forEach((t) => {
    t.classList.toggle("is-active", t.dataset.nav === activeTabFor(viewId));
  });
  if (viewId === "plan") renderPlan();
  if (viewId === "cart") renderCart();
  if (viewId === "account") renderAccountUI();
  if (viewId === "favorites") renderFavorites();
  if (viewId === "receitas") renderReceitas();
  window.scrollTo({ top: 0 });
  observeReveals();
}

/* ================= Plano (resultados) ================= */

function badgeLoja(id) {
  const s = window.STORES.find((x) => x.id === id);
  if (!s) return "";
  return `<span class="badge" style="background:${esc(s.cor)}">${esc(s.label)}</span>`;
}

function cardHTML(r, diaIndex) {
  return recipeCard(r, { dia: diaIndex });
}

function favoriteCardHTML(r) {
  return recipeCard(r, { favorite: true });
}

function browseCardHTML(r) {
  return recipeCard(r, { browse: true });
}

function recipeCard(r, opts = {}) {
  const isFav = opts.favorite === true;
  const browse = opts.browse === true;
  const diaIndex = typeof opts.dia === "number" ? opts.dia : null;
  const favActive = state.favorites.includes(r.id);
  const metodo = window.METODOS[r.id] || "fogao";
  const metodoInfo = window.METODO_LABELS[metodo] || window.METODO_LABELS.fogao;

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

  const dayShort = diaIndex != null ? ["SEG", "TER", "QUA", "QUI", "SEX", "SÁB", "DOM"][diaIndex] : "";
  const num = diaIndex != null ? String(diaIndex + 1).padStart(2, "0") : "";
  const mediaExtras = diaIndex != null
    ? `<span class="day-num">${num}</span><span class="day-day">${dayShort}</span>`
    : "";
  const eyebrow = diaIndex != null
    ? `${esc(DIAS[diaIndex])} · ${esc(r.categoria)}`
    : esc(r.categoria);
  let actions;
  if (isFav) {
    actions = `<button class="btn btn-swap" type="button" data-action="fav">☆ Remover</button>
       <button class="btn btn-primary" type="button" data-action="add-all">🛒 Adicionar à lista</button>`;
  } else if (browse) {
    actions = `<button class="btn btn-primary" type="button" data-action="add-all">🛒 Adicionar à lista</button>`;
  } else {
    actions = `<button class="btn btn-swap" type="button" data-action="swap">🔁 Trocar</button>
       <button class="btn btn-primary" type="button" data-action="add-all">🛒 Adicionar à lista</button>`;
  }

  const metodoBadge = browse
    ? `<span class="badge method">${metodoInfo.emoji} ${metodoInfo.label}</span>`
    : "";

  return `
    <article class="day-card" data-id="${esc(r.id)}" data-reveal>
      <div class="day-media">
        <img class="day-photo" src="${esc(r.foto)}" alt="${esc(r.nome)}" loading="lazy"
             referrerpolicy="no-referrer" onerror="this.onerror=null;this.src=PLACEHOLDER" />
        ${mediaExtras}
        <button class="day-fav" type="button" data-action="fav" aria-pressed="${favActive}"
                aria-label="${favActive ? "Remover dos guardados" : "Guardar receita"}">${favActive ? "★" : "☆"}</button>
      </div>
      <div class="day-body">
        <div class="day-eyebrow">${eyebrow}</div>
        <h3 class="day-title">${esc(r.nome)}</h3>
        <p class="day-sub">${esc(r.nomeOrig)}</p>
        <div class="meta">
          <span class="badge price">${money(r.preco)} / dose</span>
          <span class="badge time">⏱ ${r.tempo} min</span>
          ${algs}
          ${metodoBadge}
        </div>
        <div class="store-badges">
          ${r.lojas.map(badgeLoja).join("")}
        </div>
        <p class="dica"><strong>💡 Dica:</strong> ${esc(r.dica)}</p>
        <details class="ingredientes">
          <summary>🧾 Lista de compras (${r.ingredientes.length})</summary>
          <ul class="ing-list">${ing}</ul>
        </details>
        <div class="day-actions">${actions}</div>
      </div>
    </article>`;
}

function renderPlan() {
  const current = resolvePlan(state.planIds || []);
  const available = pool();

  const summary = $("#plan-summary");
  summary.innerHTML = `
    <div class="stat">
      <div class="num">${available.length}</div>
      <div class="lbl">receitas nos teus filtros</div>
    </div>
    <div class="stat">
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
  observeReveals();
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

/* ================= Motion (reveal + cursor) ================= */

let revealObserver = null;

function observeReveals() {
  if (!revealObserver) return;
  document.querySelectorAll("[data-reveal], [data-reveal-rise]").forEach((el) => {
    if (el.dataset.revealObserved) return;
    el.dataset.revealObserved = "1";
    const sibs = el.parentElement
      ? [...el.parentElement.children].filter((c) => c.matches("[data-reveal], [data-reveal-rise]"))
      : [];
    const idx = sibs.indexOf(el);
    if (idx > 0) el.style.transitionDelay = Math.min(idx, 6) * 55 + "ms";
    revealObserver.observe(el);
  });
}

function setupMotion() {
  if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
    document
      .querySelectorAll("[data-reveal], [data-reveal-rise]")
      .forEach((el) => el.classList.add("is-in"));
    return;
  }

  revealObserver = new IntersectionObserver(
    (entries) => {
      entries.forEach((en) => {
        if (en.isIntersecting) {
          en.target.classList.add("is-in");
          revealObserver.unobserve(en.target);
        }
      });
    },
    { threshold: 0.08, rootMargin: "0px 0px -6% 0px" }
  );

  observeReveals();
  window.addEventListener("scroll", observeReveals, { passive: true });

  // Cursor customizado (apenas desktop com rato preciso).
  if (window.matchMedia("(hover: hover) and (pointer: fine)").matches) {
    const ring = document.createElement("div");
    ring.className = "pz-cursor-ring";
    const dot = document.createElement("div");
    dot.className = "pz-cursor-dot";
    document.body.appendChild(ring);
    document.body.appendChild(dot);
    document.body.classList.add("cursor-on");

    let rx = -100, ry = -100, dx = -100, dy = -100;
    window.addEventListener(
      "pointermove",
      (e) => {
        dx = e.clientX;
        dy = e.clientY;
        dot.style.transform = `translate3d(${dx}px, ${dy}px, 0) translate(-50%, -50%)`;
      },
      { passive: true }
    );
    (function loop() {
      rx += (dx - rx) * 0.16;
      ry += (dy - ry) * 0.16;
      ring.style.transform = `translate3d(${rx}px, ${ry}px, 0) translate(-50%, -50%)`;
      requestAnimationFrame(loop);
    })();
  }
}

/* ================= Init ================= */

function init() {
  window.Auth.load();
  loadState();

  buildAllergenChips();
  buildStoreToggles();
  buildAvoidChips();
  buildMethodChips();
  bindPrice();
  updatePriceUI();
  setupPWA();
  renderAccountUI();

  /* --- Conta --- */
  $("#btn-account").addEventListener("click", () => {
    authFormMode = null;
    renderAccountUI();
    show("account");
  });
  $("#btn-settings").addEventListener("click", () => show("config"));
  $("#btn-guest").addEventListener("click", continueAsGuest);
  $("#btn-show-signup").addEventListener("click", () => {
    authFormMode = "signup";
    renderAuthForm();
    renderAccountUI();
  });
  $("#btn-show-login").addEventListener("click", () => {
    authFormMode = "login";
    renderAuthForm();
    renderAccountUI();
  });
  $("#btn-auth-cancel").addEventListener("click", () => {
    authFormMode = null;
    renderAccountUI();
  });
  $("#btn-auth-submit").addEventListener("click", handleAuthSubmit);
  $("#btn-signout").addEventListener("click", async () => {
    await window.Auth.signOut();
    window.Auth.setMode("guest");
    authFormMode = null;
    renderAccountUI();
    toast("Sessão terminada");
  });
  $("#auth-email").addEventListener("keydown", (e) => {
    if (e.key === "Enter") $("#auth-password").focus();
  });
  $("#auth-password").addEventListener("keydown", (e) => {
    if (e.key === "Enter") handleAuthSubmit();
  });

  /* --- Guardados --- */
  $("#btn-favorites").addEventListener("click", () => show("favorites"));
  $("#btn-account-favorites").addEventListener("click", () => show("favorites"));
  $("#btn-save-plan").addEventListener("click", saveCurrentPlan);
  $("#account-plans").addEventListener("click", (e) => {
    const load = e.target.closest("[data-plan-load]");
    const del = e.target.closest("[data-plan-del]");
    if (load) loadSavedPlan(load.dataset.planLoad);
    else if (del) deleteSavedPlan(del.dataset.planDel);
  });

  /* --- Alimentos a evitar --- */
  $("#btn-more-foods").addEventListener("click", () => {
    $("#food-search-input").value = "";
    renderFoodList();
    show("foods");
  });
  $("#food-search-input").addEventListener("input", renderFoodList);

  /* --- Navegação / plano --- */
  $("#btn-generate").addEventListener("click", generatePlan);
  $("#btn-regenerate").addEventListener("click", generatePlan);
  $("#btn-edit").addEventListener("click", () => show("config"));
  $("#btn-back").addEventListener("click", () => {
    if (currentView === "foods") show("config");
    else if (currentView === "favorites") show("receitas");
    else show(homeView());
  });

  /* --- Barra de navegação --- */
  document.querySelectorAll(".tab").forEach((tab) => {
    tab.addEventListener("click", () => {
      const nav = tab.dataset.nav;
      if (nav === "home") show(homeView());
      else if (nav === "receitas") show("receitas");
      else if (nav === "ingredientes") show("cart");
      else if (nav === "conta") show("account");
    });
  });

  $("#plan-days").addEventListener("click", handleRecipeAction);
  $("#favorites-list").addEventListener("click", handleRecipeAction);
  $("#receitas-list").addEventListener("click", handleRecipeAction);

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
  $("#btn-cart-back").addEventListener("click", () => show("plan"));

  updateCartBadge();
  setupMotion();

  /* --- Vista inicial: gate de conta ou app --- */
  const mode = window.Auth.getMode();
  const logged = window.Auth.isLoggedIn();
  if (!mode && !logged) {
    isGate = true;
    authFormMode = null;
    renderAccountUI();
    show("account");
  } else if (mode === "account" && !logged) {
    authFormMode = null;
    renderAccountUI();
    show("account");
  } else if (state.planIds && state.planIds.length) {
    renderPlan();
    show("plan");
  } else {
    show("config");
  }

  // Sessão guardada: renova o token e sincroniza em background.
  if (logged) {
    window.Auth.maybeRefresh().then((ok) => {
      if (!ok) {
        renderAccountUI();
        toast("Sessão expirada — entra novamente");
      } else {
        onSignedIn();
      }
    });
  }
}

document.addEventListener("DOMContentLoaded", init);
