/**
 * SmartAgri — Client API
 * Toutes les communications avec le backend FastAPI passent par ce module.
 * Base URL : https://smartagri-api-d3ga.onrender.com
 */

const API_BASE = 'https://smartagri-api-d3ga.onrender.com';

/* ───────────────────────────────────────────
   GESTION DU TOKEN JWT
──────────────────────────────────────────── */
const Auth = {
  getToken()  { return localStorage.getItem('smartagri_token'); },
  setToken(t) { localStorage.setItem('smartagri_token', t); },
  removeToken(){ localStorage.removeItem('smartagri_token'); },

  getUser()   {
    try { return JSON.parse(localStorage.getItem('smartagri_user')); }
    catch { return null; }
  },
  setUser(u)  { localStorage.setItem('smartagri_user', JSON.stringify(u)); },
  removeUser(){ localStorage.removeItem('smartagri_user'); },

  isLoggedIn(){ return !!this.getToken(); },

  logout() {
    this.removeToken();
    this.removeUser();
    // Calcule le chemin vers login/index.html
    // depuis n'importe quelle profondeur (file:// ou serveur local)
    const base = window.location.href;
    const pagesIdx = base.indexOf('/pages/');
    if (pagesIdx !== -1) {
      // On est dans frontend/app/pages/ → remonter de 3 niveaux
      window.location.replace('../../login/index.html');
    } else {
      // Fallback absolu (racine du site déployé)
      window.location.replace('/login/index.html');
    }
  },
};

/* ───────────────────────────────────────────
   REQUÊTE DE BASE
──────────────────────────────────────────── */
async function request(method, path, body = null, auth = true) {
  const headers = { 'Content-Type': 'application/json' };

  if (auth) {
    const token = Auth.getToken();
    if (!token) { Auth.logout(); return; }
    headers['Authorization'] = `Bearer ${token}`;
  }

  const config = { method, headers };
  if (body) config.body = JSON.stringify(body);

  const response = await fetch(`${API_BASE}${path}`, config);

  // Token expiré → redirection login
  if (response.status === 401) {
    Auth.logout();
    return;
  }

  if (response.status === 204) return null; // No content

  const data = await response.json();

  if (!response.ok) {
    const message = data?.detail || 'Une erreur est survenue.';
    throw new Error(Array.isArray(message)
      ? message.map(e => e.msg).join(', ')
      : message
    );
  }

  return data;
}

/* ───────────────────────────────────────────
   ENDPOINTS AUTH
──────────────────────────────────────────── */
const ApiAuth = {
  async register(payload) {
    return request('POST', '/api/auth/register', payload, false);
  },
  async login(email, password) {
    return request('POST', '/api/auth/login', { email, password }, false);
  },
  async me() {
    return request('GET', '/api/auth/me');
  },
};

/* ───────────────────────────────────────────
   ENDPOINTS PARCELLES
──────────────────────────────────────────── */
const ApiParcelles = {
  async list()          { return request('GET',    '/api/parcelles/'); },
  async get(id)         { return request('GET',    `/api/parcelles/${id}`); },
  async create(payload) { return request('POST',   '/api/parcelles/', payload); },
  async update(id, p)   { return request('PUT',    `/api/parcelles/${id}`, p); },
  async delete(id)      { return request('DELETE', `/api/parcelles/${id}`); },
};

/* ───────────────────────────────────────────
   ENDPOINTS PRÉDICTION
──────────────────────────────────────────── */
const ApiPrediction = {
  async predict(payload)  { return request('POST', '/api/prediction/', payload); },
  async historique()      { return request('GET',  '/api/prediction/historique'); },
};

/* ───────────────────────────────────────────
   ENDPOINTS MÉTÉO
──────────────────────────────────────────── */
const ApiMeteo = {
  async current(ville)    { return request('GET', `/api/meteo/${encodeURIComponent(ville)}`, null, false); },
  async previsions(ville) { return request('GET', `/api/meteo/${encodeURIComponent(ville)}/previsions`, null, false); },
};

/* ───────────────────────────────────────────
   ENDPOINTS AGRIBOT
──────────────────────────────────────────── */
const ApiAgribot = {
  async sendMessage(content)  { return request('POST',   '/api/agribot/message', { content }); },
  async historique()          { return request('GET',    '/api/agribot/historique'); },
  async clearHistory()        { return request('DELETE', '/api/agribot/historique'); },
};

/* ───────────────────────────────────────────
   UI HELPERS
──────────────────────────────────────────── */

/** Afficher un toast de notification */
function showToast(message, type = 'success', duration = 3500) {
  let container = document.getElementById('toast-container');
  if (!container) {
    container = document.createElement('div');
    container.id = 'toast-container';
    document.body.appendChild(container);
  }
  const icons = { success: '✅', error: '❌', warning: '⚠️', info: 'ℹ️' };
  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.innerHTML = `<span>${icons[type] || 'ℹ️'}</span><span>${message}</span>`;
  container.appendChild(toast);
  setTimeout(() => {
    toast.style.animation = 'toastOut .25s ease forwards';
    setTimeout(() => toast.remove(), 300);
  }, duration);
}

/** Afficher / masquer un spinner sur un bouton */
function setButtonLoading(btn, loading, originalText = '') {
  if (loading) {
    btn.disabled = true;
    btn.dataset.originalText = btn.innerHTML;
    btn.innerHTML = `<span class="btn-spinner"></span>`;
  } else {
    btn.disabled = false;
    btn.innerHTML = originalText || btn.dataset.originalText || btn.innerHTML;
  }
}

/** Formatter une date en français */
function formatDate(isoString) {
  if (!isoString) return '—';
  return new Date(isoString).toLocaleDateString('fr-FR', {
    day: '2-digit', month: 'short', year: 'numeric',
    hour: '2-digit', minute: '2-digit',
  });
}

/** Formatter une date courte */
function formatDateShort(isoString) {
  if (!isoString) return '—';
  return new Date(isoString).toLocaleDateString('fr-FR', {
    day: '2-digit', month: 'short', year: 'numeric',
  });
}

/** Confirmer une action destructive */
function confirmAction(message) {
  return window.confirm(message);
}

/** Initialiser la topbar (avatar + menu) avec les données utilisateur */
function initTopbar() {
  const user = Auth.getUser();

  // ── BUG CORRIGÉ : on branche TOUJOURS btn-logout, même si user est null
  // Ainsi la déconnexion fonctionne même si le localStorage est corrompu.
  document.getElementById('btn-logout')?.addEventListener('click', () => Auth.logout());

  // Mobile menu toggle — branché sans dépendance à user
  document.getElementById('menu-toggle')?.addEventListener('click', () => {
    document.getElementById('sidebar')?.classList.toggle('open');
  });

  // Fermer le dropdown en cliquant ailleurs
  document.addEventListener('click', (e) => {
    if (!e.target.closest('.avatar-wrap')) {
      document.getElementById('user-dropdown')?.classList.remove('open');
    }
  });

  if (!user) return; // Les éléments visuels ne sont remplis que si user existe

  // Initiales avatar
  const avatarEl = document.getElementById('topbar-avatar');
  if (avatarEl) {
    const initials = (user.firstname?.[0] || '') + (user.lastname?.[0] || '');
    avatarEl.textContent = initials.toUpperCase() || '?';
    avatarEl.title = `${user.firstname} ${user.lastname}`;
  }

  // Nom dans le dropdown
  const dropName  = document.getElementById('drop-name');
  const dropEmail = document.getElementById('drop-email');
  const dropRole  = document.getElementById('drop-role');
  if (dropName)  dropName.textContent  = `${user.firstname} ${user.lastname}`;
  if (dropEmail) dropEmail.textContent = user.email;
  if (dropRole)  dropRole.textContent  = user.role;

  // Toggle dropdown au clic sur l'avatar
  if (avatarEl) {
    avatarEl.addEventListener('click', (e) => {
      e.stopPropagation();
      document.getElementById('user-dropdown')?.classList.toggle('open');
    });
  }
}

/** Vérifier l'authentification — rediriger si non connecté */
function requireAuth() {
  if (!Auth.isLoggedIn()) {
    Auth.logout();
  }
}

/** Marquer le lien actif dans la sidebar */
function setActiveNav(pageId) {
  document.querySelectorAll('.nav-link').forEach(link => {
    link.classList.toggle('active', link.dataset.page === pageId);
  });
}

/** Convertir le markdown simple en HTML (pour AgriBot) */
function markdownToHtml(text) {
  return text
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/`(.*?)`/g, '<code>$1</code>')
    .replace(/\n\n/g, '</p><p>')
    .replace(/\n/g, '<br>')
    .replace(/^/, '<p>')
    .replace(/$/, '</p>')
    .replace(/\| (.+?) \|/g, (m) => `<td>${m.slice(2,-2)}</td>`)
    .replace(/^## (.*)/gm, '<h3>$1</h3>')
    .replace(/^• (.*)/gm, '<li>$1</li>');
}

/** Icône météo OpenWeatherMap → emoji */
function meteoIcon(code) {
  if (!code) return '🌤️';
  const map = {
    '01': '☀️', '02': '⛅', '03': '☁️', '04': '☁️',
    '09': '🌧️', '10': '🌦️', '11': '⛈️', '13': '❄️', '50': '🌫️',
  };
  return map[code.slice(0,2)] || '🌤️';
}
