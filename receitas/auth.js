/* Prato da Semana — conta + sincronização (Supabase Auth + user_data).
   Sem SDK externo: usa fetch diretamente contra GoTrue e PostgREST.
   - Guest: tudo fica no localStorage.
   - Conta: preferências, ementa, lista de compras, guardados e ementas
     guardadas são sincronizados na nuvem (tabela user_data, protegida por RLS). */

window.Auth = (() => {
  const URL = (window.SUPABASE && window.SUPABASE.url) || "";
  const KEY = (window.SUPABASE && window.SUPABASE.anonKey) || "";
  const STORAGE = "prato-da-semana:auth:v1";
  const MODE_KEY = "prato-da-semana:auth-mode:v1"; // "guest" | "account"

  let session = null;

  function load() {
    try {
      session = JSON.parse(localStorage.getItem(STORAGE)) || null;
    } catch (e) {
      session = null;
    }
    return session;
  }

  function persist() {
    try {
      if (session) localStorage.setItem(STORAGE, JSON.stringify(session));
      else localStorage.removeItem(STORAGE);
    } catch (e) {
      /* ignore */
    }
  }

  function isLoggedIn() {
    return !!(session && session.user && session.access_token);
  }

  function email() {
    return session && session.user ? session.user.email : "";
  }

  function getMode() {
    try {
      return localStorage.getItem(MODE_KEY);
    } catch (e) {
      return null;
    }
  }

  function setMode(m) {
    try {
      localStorage.setItem(MODE_KEY, m);
    } catch (e) {
      /* ignore */
    }
  }

  async function post(path, body, headers = {}) {
    let res;
    try {
      res = await fetch(URL + path, {
        method: "POST",
        headers: { apikey: KEY, "Content-Type": "application/json", ...headers },
        body: JSON.stringify(body),
      });
    } catch (e) {
      return { ok: false, status: 0, data: { msg: "Sem ligação à internet." } };
    }
    let data = null;
    try {
      data = await res.json();
    } catch (e) {
      data = null;
    }
    return { ok: res.ok, status: res.status, data };
  }

  function authError(data) {
    if (!data) return "Erro de autenticação. Tenta novamente.";
    const msg = data.msg || data.message || data.error_description || data.error;
    return msg || "Erro de autenticação. Tenta novamente.";
  }

  async function signUp(emailValue, password) {
    const res = await post("/auth/v1/signup", { email: emailValue, password });
    if (!res.ok) return { ok: false, error: authError(res.data) };
    // Com confirmação de email ativa, a resposta vem sem session.
    if (res.data && res.data.access_token) {
      session = {
        access_token: res.data.access_token,
        refresh_token: res.data.refresh_token,
        expires_at: res.data.expires_at,
        user: res.data.user,
      };
      persist();
      return { ok: true, needsConfirm: false };
    }
    return { ok: true, needsConfirm: true };
  }

  async function signIn(emailValue, password) {
    const res = await post("/auth/v1/token?grant_type=password", {
      email: emailValue,
      password,
    });
    if (!res.ok) return { ok: false, error: authError(res.data) };
    session = {
      access_token: res.data.access_token,
      refresh_token: res.data.refresh_token,
      expires_at: res.data.expires_at,
      user: res.data.user,
    };
    persist();
    return { ok: true };
  }

  async function refresh() {
    if (!session || !session.refresh_token) return false;
    const res = await post("/auth/v1/token?grant_type=refresh_token", {
      refresh_token: session.refresh_token,
    });
    if (!res.ok) {
      session = null;
      persist();
      return false;
    }
    session = {
      access_token: res.data.access_token,
      refresh_token: res.data.refresh_token,
      expires_at: res.data.expires_at,
      user: res.data.user,
    };
    persist();
    return true;
  }

  // Atualiza o token se já estiver expirado.
  async function maybeRefresh() {
    if (!session || !session.access_token) return false;
    const exp = session.expires_at ? Number(session.expires_at) : 0;
    if (exp && Date.now() / 1000 > exp - 30) return refresh();
    return true;
  }

  async function signOut() {
    if (session && session.access_token) {
      try {
        await fetch(URL + "/auth/v1/logout", {
          method: "POST",
          headers: { apikey: KEY, Authorization: `Bearer ${session.access_token}` },
        });
      } catch (e) {
        /* ignore */
      }
    }
    session = null;
    persist();
  }

  /* ---------------- Dados na nuvem (user_data) ---------------- */

  async function authorizedFetch(path, options = {}) {
    if (!isLoggedIn()) return null;
    const doFetch = (token) =>
      fetch(URL + path, {
        ...options,
        headers: {
          apikey: KEY,
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
          ...(options.headers || {}),
        },
      });
    let r = await doFetch(session.access_token);
    if (r.status === 401) {
      const ok = await refresh();
      if (!ok) return null;
      r = await doFetch(session.access_token);
    }
    return r;
  }

  async function getAllData() {
    if (!isLoggedIn()) return {};
    const r = await authorizedFetch("/rest/v1/user_data?select=key,value");
    if (!r || !r.ok) return {};
    let rows;
    try {
      rows = await r.json();
    } catch (e) {
      return {};
    }
    const map = {};
    (rows || []).forEach((row) => {
      map[row.key] = row.value;
    });
    return map;
  }

  async function getData(key) {
    const r = await authorizedFetch(
      `/rest/v1/user_data?select=value&key=eq.${encodeURIComponent(key)}`
    );
    if (!r || !r.ok) return null;
    let rows;
    try {
      rows = await r.json();
    } catch (e) {
      return null;
    }
    return rows && rows.length ? rows[0].value : null;
  }

  async function setData(key, value) {
    if (!isLoggedIn()) return false;
    const body = {
      user_id: session.user.id,
      key,
      value,
      updated_at: new Date().toISOString(),
    };
    const r = await authorizedFetch("/rest/v1/user_data?on_conflict=user_id,key", {
      method: "POST",
      headers: { Prefer: "return=minimal" },
      body: JSON.stringify(body),
    });
    return !!(r && r.ok);
  }

  return {
    load,
    isLoggedIn,
    email,
    getMode,
    setMode,
    signUp,
    signIn,
    signOut,
    maybeRefresh,
    getAllData,
    getData,
    setData,
  };
})();
