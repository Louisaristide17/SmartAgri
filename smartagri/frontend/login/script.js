/* ============================================================
   SmartAgri – Login Page Script
   Connecté au backend FastAPI via api.js
   ============================================================ */

/* ── Navigation entre onglets ── */
function showTab(tab) {
  ['login', 'register', 'forgot'].forEach(id => {
    const panel = document.getElementById(`panel-${id}`);
    const btn   = document.getElementById(`tab-${id}`);
    if (panel) panel.style.display = (id === tab) ? 'block' : 'none';
    if (btn)   btn.classList.toggle('active', id === tab);
  });
  clearErrors();
}

/* ── Afficher / masquer mot de passe ── */
function toggleEye(inputId, btn) {
  const input = document.getElementById(inputId);
  if (!input) return;
  input.type = input.type === 'password' ? 'text' : 'password';
  btn.textContent = input.type === 'password' ? '👁' : '🙈';
}

/* ── Indicateur de force du mot de passe ── */
document.getElementById('r-pwd')?.addEventListener('input', function () {
  const val  = this.value;
  const meter = document.getElementById('pwd-meter');
  const fill  = document.getElementById('pwd-fill');
  const label = document.getElementById('pwd-label');
  if (!meter) return;

  if (!val) { meter.style.display = 'none'; return; }
  meter.style.display = 'flex';

  let score = 0;
  if (val.length >= 8)  score++;
  if (val.length >= 12) score++;
  if (/[A-Z]/.test(val)) score++;
  if (/[0-9]/.test(val)) score++;
  if (/[^A-Za-z0-9]/.test(val)) score++;

  const levels = [
    { pct: 20,  color: '#ef4444', text: 'Très faible', textColor: '#ef4444' },
    { pct: 40,  color: '#f97316', text: 'Faible',      textColor: '#f97316' },
    { pct: 60,  color: '#eab308', text: 'Moyen',       textColor: '#eab308' },
    { pct: 80,  color: '#22c55e', text: 'Fort',        textColor: '#22c55e' },
    { pct: 100, color: '#16a34a', text: 'Très fort',   textColor: '#16a34a' },
  ];
  const lvl = levels[Math.min(score - 1, 4)] || levels[0];
  fill.style.width      = lvl.pct + '%';
  fill.style.background = lvl.color;
  label.textContent     = lvl.text;
  label.style.color     = lvl.textColor;
});

/* ── Utilitaires validation ── */
function isEmail(v) { return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v.trim()); }

function setError(id, msg) {
  const el = document.getElementById(id);
  if (el) el.textContent = msg;
  const input = document.querySelector(`[id="${id.replace('err-', '')}"]`);
  if (input) input.classList.toggle('invalid', !!msg);
}

function clearErrors() {
  document.querySelectorAll('.ferr').forEach(el => el.textContent = '');
  document.querySelectorAll('.finput').forEach(el => el.classList.remove('invalid'));
  document.querySelectorAll('.form-alert').forEach(el => {
    el.style.display = 'none'; el.className = 'form-alert';
  });
}

function showAlert(id, message, type = 'error') {
  const el = document.getElementById(id);
  if (!el) return;
  el.textContent  = message;
  el.className    = `form-alert ${type}`;
  el.style.display = 'block';
}

/* ── Spinner bouton ── */
function setLoading(btnId, on) {
  const btn = document.getElementById(btnId);
  if (!btn) return;
  if (on) {
    btn.disabled = true;
    btn._orig = btn.innerHTML;
    btn.innerHTML = '<span class="btn-spinner"></span>';
  } else {
    btn.disabled = false;
    btn.innerHTML = btn._orig || btn.innerHTML;
  }
}

/* ═══════════════════════════════════
   CONNEXION
═══════════════════════════════════ */
document.getElementById('login-form')?.addEventListener('submit', async (e) => {
  e.preventDefault();
  clearErrors();

  const email = document.getElementById('l-email').value.trim();
  const pwd   = document.getElementById('l-pwd').value;
  let ok = true;

  if (!email)         { setError('err-l-email', 'E-mail requis.'); ok = false; }
  else if (!isEmail(email)) { setError('err-l-email', 'Format d\'e-mail invalide.'); ok = false; }
  if (!pwd)           { setError('err-l-pwd', 'Mot de passe requis.'); ok = false; }
  if (!ok) return;

  setLoading('btn-login', true);
  try {
    const data = await ApiAuth.login(email, pwd);
    Auth.setToken(data.access_token);
    Auth.setUser(data.user);

    showPlatformChoice(data.user.firstname);
  } catch (err) {
    showAlert('login-alert', '❌ ' + err.message);
  } finally {
    setLoading('btn-login', false);
  }
});

/* ═══════════════════════════════════
   INSCRIPTION
═══════════════════════════════════ */
document.getElementById('register-form')?.addEventListener('submit', async (e) => {
  e.preventDefault();
  clearErrors();

  const fn      = document.getElementById('r-fn').value.trim();
  const ln      = document.getElementById('r-ln').value.trim();
  const email   = document.getElementById('r-email').value.trim();
  const phone   = document.getElementById('r-phone').value.trim();
  const role    = document.getElementById('r-role').value;
  const pwd     = document.getElementById('r-pwd').value;
  const confirm = document.getElementById('r-confirm').value;
  const terms   = document.getElementById('r-terms').checked;

  let ok = true;

  if (!fn)    { setError('err-r-fn',   'Prénom requis.'); ok = false; }
  if (!ln)    { setError('err-r-ln',   'Nom requis.'); ok = false; }
  if (!email || !isEmail(email)) { setError('err-r-email', 'E-mail invalide.'); ok = false; }
  if (!role)  { setError('err-r-role', 'Sélectionnez votre profil.'); ok = false; }
  if (pwd.length < 8) { setError('err-r-pwd', 'Minimum 8 caractères.'); ok = false; }
  if (pwd !== confirm){ setError('err-r-confirm', 'Les mots de passe ne correspondent pas.'); ok = false; }
  if (!terms) { setError('err-r-terms', 'Vous devez accepter les conditions.'); ok = false; }
  if (!ok) return;

  setLoading('btn-register', true);
  try {
    const data = await ApiAuth.register({ firstname: fn, lastname: ln, email, phone, role, password: pwd });
    Auth.setToken(data.access_token);
    Auth.setUser(data.user);
    showAlert('register-alert', '✅ Compte créé ! Redirection...', 'success');
    setTimeout(() => goToApp('web'), 1500);
  } catch (err) {
    showAlert('register-alert', '❌ ' + err.message);
  } finally {
    setLoading('btn-register', false);
  }
});

/* ═══════════════════════════════════
   MOT DE PASSE OUBLIÉ
═══════════════════════════════════ */
document.getElementById('forgot-form')?.addEventListener('submit', async (e) => {
  e.preventDefault();
  clearErrors();

  const email = document.getElementById('f-email').value.trim();
  if (!isEmail(email)) { setError('err-f-email', 'E-mail invalide.'); return; }

  // Simulation (endpoint non implémenté)
  showAlert('forgot-alert',
    `✅ Un lien a été envoyé à ${email}. Vérifiez votre boîte mail.`, 'success');
  document.getElementById('forgot-form').reset();
});

/* ── Connexion sociale (démo) ── */
function socialDemo(provider) {
  alert(`Connexion avec ${provider} — connectez votre OAuth dans le backend FastAPI.`);
}

/* ── Choix de la plateforme (Web / Mobile) : toujours proposé après connexion ── */
function showPlatformChoice(prenom) {
  document.getElementById('login-form').style.display = 'none';
  ['.or-divider', '.social-row', '.alert-demo', '.row-sb'].forEach(sel => {
    const el = document.querySelector(sel); if (el) el.style.display = 'none';
  });
  document.getElementById('session-box')?.remove();
  showAlert('login-alert', `✅ Bienvenue ${prenom || ''} ! Choisissez votre plateforme ci-dessous.`, 'success');
  document.getElementById('platform-box').style.display = 'block';
}

/* ── Redirection après connexion ── */
function goToApp(platform) {
  if (platform === 'web') {
    window.location.href = '../app/pages/dashboard.html';
  } else if (platform === 'mobile') {
    // Téléchargement direct de l'APK Android
    const a = document.createElement('a');
    a.href = '../mobile/smartagri.apk';
    a.download = 'smartagri.apk';
    document.body.appendChild(a);
    a.click();
    a.remove();
    // Message de confirmation
    showAlert('login-alert', '📥 Téléchargement de l\'APK lancé. Installez-le sur votre téléphone Android (autorisez "Sources inconnues").', 'success');
  }
}

/* ── Pré-remplir email mémorisé ── */
window.addEventListener('DOMContentLoaded', async () => {
  const user = Auth.getUser();
  if (user?.email) {
    const emailInput = document.getElementById('l-email');
    if (emailInput) emailInput.value = user.email;
  }
  // La page de connexion s'affiche toujours : on ne saute plus directement dans l'application.
  // Si une session valide existe déjà, on propose de la poursuivre.
  if (!Auth.isLoggedIn()) return;
  try {
    const me = await request('GET', '/api/auth/me');
    const box = document.createElement('div');
    box.id = 'session-box';
    box.className = 'form-alert success';
    box.style.cssText = 'display:block;margin-bottom:14px;';
    box.innerHTML = `Session ouverte : <strong>${me.firstname || me.email}</strong> ` +
      `<button type="button" id="btn-continue" style="margin-left:8px;cursor:pointer">Continuer</button> ` +
      `<button type="button" id="btn-switch" style="margin-left:4px;cursor:pointer">Changer de compte</button>`;
    const form = document.getElementById('login-form');
    form.parentNode.insertBefore(box, form);
    document.getElementById('btn-continue').onclick = () => showPlatformChoice(me.firstname);
    document.getElementById('btn-switch').onclick = () => { Auth.removeToken(); Auth.removeUser(); box.remove(); };
  } catch (e) {
    Auth.removeToken(); Auth.removeUser();   // jeton périmé : on repart de zéro
  }
});

