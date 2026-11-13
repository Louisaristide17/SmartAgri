/* ============================================================
   SmartAgri Mobile — app.js
   Navigation, données, chat, prédiction, météo
   ============================================================ */

/* ═══════════════════════════════════════
   INIT & SPLASH
═══════════════════════════════════════ */
window.addEventListener('DOMContentLoaded', async () => {
  // Vérifier authentification
  if (!Auth.isLoggedIn()) {
    window.location.href = '../login/index.html';
    return;
  }
  try { await request('GET', '/api/auth/me'); }          // jeton invalide ou expiré -> retour à la connexion
  catch (e) { if (!Auth.isLoggedIn()) return; }          // (request() déconnecte seule sur 401)

  // Splash → app après 1.6s (durée de la barre)
  await sleep(1700);
  document.getElementById('splash').classList.add('hidden');
  document.getElementById('app').style.display = 'flex';

  // Init interface
  initMobileTopbar();
  showPage('accueil');
  loadAccueil();
  loadParcellesData();
  loadPredHistory();
  loadChatHistory();
});

function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

/* ═══════════════════════════════════════
   NAVIGATION
═══════════════════════════════════════ */
const PAGE_TITLES = {
  accueil:'SmartAgri', parcelles:'Mes Parcelles', prediction:'Prédiction IA',
  agribot:'AgriBot', meteo:'Météo', profil:'Profil',
  notifications:'Notifications',
};

let pageHistory = ['accueil'];

function showPage(pageId) {
  // Masquer toutes les pages
  document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));

  const page = document.getElementById(`page-${pageId}`);
  if (!page) return;
  page.classList.add('active');

  // Topbar
  const isHome = pageId === 'accueil';
  document.getElementById('back-btn').style.display   = isHome ? 'none' : 'flex';
  document.getElementById('topbar-logo').style.display = isHome ? 'flex' : 'none';
  document.getElementById('topbar-title').style.display = isHome ? 'none' : 'block';
  document.getElementById('topbar-title').textContent  = PAGE_TITLES[pageId] || pageId;

  // Bottom nav
  document.querySelectorAll('.bnav-item').forEach(b => {
    b.classList.toggle('active', b.dataset.page === pageId);
  });

  // Historique
  if (pageHistory[pageHistory.length - 1] !== pageId) {
    pageHistory.push(pageId);
  }

  // Charger données selon page
  if (pageId === 'meteo')   loadMMeteo('Abidjan', null);
  if (pageId === 'parcelles') renderMParcelles();
  if (pageId === 'profil')  loadProfil();
}

function goBack() {
  pageHistory.pop();
  const prev = pageHistory[pageHistory.length - 1] || 'accueil';
  pageHistory.pop(); // sera re-ajouté par showPage
  showPage(prev);
}

/* ═══════════════════════════════════════
   TOPBAR
═══════════════════════════════════════ */
function initMobileTopbar() {
  const user = Auth.getUser();
  if (!user) return;
  const initials = ((user.firstname?.[0] || '') + (user.lastname?.[0] || '')).toUpperCase();
  document.getElementById('topbar-avatar').textContent = initials;
  document.getElementById('prof-avatar').textContent   = initials;
  document.getElementById('prof-name').textContent     = `${user.firstname} ${user.lastname}`;
  document.getElementById('prof-role').textContent     = user.role || 'Agriculteur';
  document.getElementById('prof-email').textContent    = user.email;
}

/* ═══════════════════════════════════════
   PAGE ACCUEIL
═══════════════════════════════════════ */
async function loadAccueil() {
  const user = Auth.getUser();

  // Salutation
  const h = new Date().getHours();
  const salut = h < 12 ? 'Bonjour' : h < 18 ? 'Bon après-midi' : 'Bonsoir';
  document.getElementById('greeting').textContent =
    `${salut}, ${user?.firstname || ''} 👋`;

  const opts = { weekday:'long', day:'numeric', month:'long' };
  document.getElementById('greeting-date').textContent =
    new Date().toLocaleDateString('fr-FR', opts);

  // Météo bannière
  loadMeteoBanner();

  // Stats
  try {
    const [parcelles, preds] = await Promise.all([
      ApiParcelles.list(),
      ApiPrediction.historique(),
    ]);
    document.getElementById('stat-parcelles').textContent = parcelles.length;
    document.getElementById('stat-preds').textContent     = preds.length;

    if (preds.length > 0) {
      const avg = (preds.reduce((s, p) => s + p.rendement_predit, 0) / preds.length).toFixed(1);
      document.getElementById('stat-rendement').textContent = avg;
    } else {
      document.getElementById('stat-rendement').textContent = '–';
    }

    // Aperçu parcelles
    const prev = document.getElementById('parcelles-preview');
    const icons = {cacao:'🍫',cafe:'☕',hevea:'🌳',palmier:'🌴',anacarde:'🥜',coton:'☁️',mais:'🌽',riz:'🌾',manioc:'🥔',igname:'🍠',arachide:'🥜',sorgho:'🌿',mil:'🌿'};
    if (parcelles.length === 0) {
      prev.innerHTML = `<div style="text-align:center;padding:16px;color:var(--gray400);font-size:.85rem;">
        Aucune parcelle — <button onclick="showPage('parcelles')" style="background:none;border:none;color:var(--g500);font-weight:600;cursor:pointer;">Ajouter</button></div>`;
    } else {
      prev.innerHTML = parcelles.slice(0,3).map(p => `
        <div class="parcelle-preview-card" onclick="showPage('parcelles')">
          <div class="ppc-left">
            <div class="ppc-icon">${icons[p.culture]||'🌱'}</div>
            <div class="ppc-info">
              <div class="ppc-name">${p.nom}</div>
              <div class="ppc-meta">${p.culture} · ${p.superficie} ha · ${p.ville||'–'}</div>
            </div>
          </div>
          <div class="ppc-right">›</div>
        </div>`).join('');
    }

    // Dernière prédiction
    const lastPred = document.getElementById('last-prediction');
    if (preds.length > 0) {
      const lp = preds[0];
      lastPred.innerHTML = `
        <div class="last-pred-card">
          <div class="lpc-label">Dernière prédiction</div>
          <div class="lpc-value">${lp.rendement_predit.toFixed(2)}</div>
          <div class="lpc-unit">tonnes / hectare</div>
          <div class="lpc-culture">${icons[lp.culture]||'🌱'} ${lp.culture} · ${lp.superficie} ha</div>
        </div>`;
    } else {
      lastPred.innerHTML = `<div style="text-align:center;padding:14px;color:var(--gray400);font-size:.84rem;">
        Aucune prédiction — <button onclick="showPage('prediction')" style="background:none;border:none;color:var(--g500);font-weight:600;cursor:pointer;">Prédire maintenant</button></div>`;
    }
  } catch(e) {
    console.error(e);
  }
}

async function loadMeteoBanner() {
  try {
    const m = await ApiMeteo.current('Abidjan');
    document.getElementById('mb-icon').textContent = meteoIcon(m.icone);
    document.getElementById('mb-temp').textContent = m.temperature + '°C';
    document.getElementById('mb-desc').textContent = m.description;
    document.getElementById('mb-city').textContent = m.ville;
  } catch(e) {}
}

/* ═══════════════════════════════════════
   PAGE PARCELLES
═══════════════════════════════════════ */
let allMParcelles = [];
let mFilter = 'all';

async function loadParcellesData() {
  try {
    allMParcelles = await ApiParcelles.list();
    renderMParcelles();
    // Alimenter le select prédiction
    const sel = document.getElementById('m-sel-parcelle');
    sel.innerHTML = '<option value="">Sélectionner une parcelle…</option>';
    allMParcelles.forEach(p => {
      sel.innerHTML += `<option value="${p.id}" data-culture="${p.culture}" data-sol="${p.type_sol}" data-sup="${p.superficie}" data-ville="${p.ville||''}">${p.nom}</option>`;
    });
  } catch(e) {}
}

function renderMParcelles(list = null) {
  const data = list || allMParcelles;
  const q    = document.getElementById('m-search')?.value?.toLowerCase() || '';
  let filtered = data;

  if (mFilter !== 'all') {
    filtered = filtered.filter(p => p.statut === mFilter || p.culture === mFilter);
  }
  if (q) {
    filtered = filtered.filter(p =>
      p.nom.toLowerCase().includes(q) || p.culture.includes(q) || (p.ville||'').toLowerCase().includes(q));
  }

  const icons = {cacao:'🍫',cafe:'☕',hevea:'🌳',palmier:'🌴',anacarde:'🥜',coton:'☁️',mais:'🌽',riz:'🌾',manioc:'🥔',igname:'🍠',arachide:'🥜',sorgho:'🌿',mil:'🌿'};
  const sbadge = {active:'mb-green',en_repos:'mb-orange',recoltee:'mb-blue'};
  const sfr    = {active:'Active',en_repos:'En repos',recoltee:'Récoltée'};
  const solfr  = {sableux:'Sableux',argileux:'Argileux',limoneux:'Limoneux',lateritique:'Latéritique'};

  const container = document.getElementById('m-parcelles-list');
  if (filtered.length === 0) {
    container.innerHTML = `<div style="text-align:center;padding:40px 16px;color:var(--gray400);">
      <div style="font-size:2.5rem;margin-bottom:10px;">🌾</div>
      <div style="font-weight:600;margin-bottom:6px;">Aucune parcelle</div>
      <div style="font-size:.82rem;">Appuyez sur + pour en ajouter une</div>
    </div>`;
    return;
  }

  container.innerHTML = filtered.map(p => `
    <div class="m-parcelle-card">
      <div class="mpc-header">
        <div>
          <div class="mpc-title">${icons[p.culture]||'🌱'} ${p.nom}</div>
          <div class="mpc-sub">${p.ville || 'Localisation non renseignée'}</div>
        </div>
        <span class="m-badge ${sbadge[p.statut]||'mb-gray'}">${sfr[p.statut]||p.statut}</span>
      </div>
      <div class="mpc-meta">
        <div class="mpc-meta-item"><span class="mpc-meta-lbl">Culture</span><span class="mpc-meta-val">${p.culture}</span></div>
        <div class="mpc-meta-item"><span class="mpc-meta-lbl">Superficie</span><span class="mpc-meta-val">${p.superficie} ha</span></div>
        <div class="mpc-meta-item"><span class="mpc-meta-lbl">Sol</span><span class="mpc-meta-val">${solfr[p.type_sol]||p.type_sol}</span></div>
        <div class="mpc-meta-item"><span class="mpc-meta-lbl">Ajoutée</span><span class="mpc-meta-val">${formatDateShort(p.created_at)}</span></div>
      </div>
      <div class="mpc-actions">
        <button class="mpc-btn mpc-btn-pred"   onclick="mQuickPredict(${p.id})">🔮 Prédire</button>
        <button class="mpc-btn mpc-btn-edit"   onclick="mEditParcelle(${p.id})">✏️</button>
        <button class="mpc-btn mpc-btn-delete" onclick="mDeleteParcelle(${p.id},'${p.nom}')">🗑️</button>
      </div>
    </div>`).join('');
}

function filterMParcelles() { renderMParcelles(); }

function setMFilter(f, btn) {
  mFilter = f;
  document.querySelectorAll('#filter-chips .chip').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  renderMParcelles();
}

/* ── Drawer parcelle ── */
function openAddParcelle() {
  document.getElementById('d-edit-id').value = '';
  document.getElementById('drawer-title').textContent = 'Nouvelle parcelle';
  document.getElementById('parcelle-drawer').querySelector('form')?.reset();
  document.querySelectorAll('.m-err').forEach(e => e.textContent='');
  document.getElementById('drawer-alert').style.display = 'none';
  ['d-nom','d-sup','d-statut','d-culture','d-sol','d-ville','d-desc'].forEach(id => {
    const el = document.getElementById(id); if (el) el.value = '';
  });
  document.getElementById('d-statut').value = 'active';
  _gps = null; const gi = document.getElementById('d-gps-info'); if (gi) gi.textContent = '';
  openDrawer();
}

async function mEditParcelle(id) {
  try {
    const p = await ApiParcelles.get(id);
    document.getElementById('d-edit-id').value  = p.id;
    document.getElementById('drawer-title').textContent = 'Modifier la parcelle';
    document.getElementById('d-nom').value      = p.nom;
    document.getElementById('d-sup').value      = p.superficie;
    document.getElementById('d-statut').value   = p.statut;
    document.getElementById('d-culture').value  = p.culture;
    document.getElementById('d-sol').value      = p.type_sol;
    document.getElementById('d-ville').value    = p.ville || '';
    document.getElementById('d-desc').value     = p.description || '';
    openDrawer();
  } catch(e) { mToast('Erreur de chargement', 'error'); }
}

async function mDeleteParcelle(id, nom) {
  if (!confirm(`Supprimer "${nom}" ?`)) return;
  try {
    await ApiParcelles.delete(id);
    mToast('Parcelle supprimée', 'success');
    loadParcellesData();
  } catch(e) { mToast('Erreur : ' + e.message, 'error'); }
}

let _gps = null;   // {latitude, longitude} du téléphone
function mUseGps() {
  const info = document.getElementById('d-gps-info');
  if (!navigator.geolocation) { info.textContent = 'GPS non disponible sur cet appareil.'; return; }
  info.textContent = 'Recherche de votre position…';
  navigator.geolocation.getCurrentPosition(async pos => {
    _gps = { latitude: +pos.coords.latitude.toFixed(5), longitude: +pos.coords.longitude.toFixed(5) };
    try {
      const z = await ApiPrediction.zoneGps(_gps.latitude, _gps.longitude);
      if (!z.dans_le_pays) { info.textContent = '⚠️ ' + z.message; _gps = null; return; }
      info.textContent = `📍 ${z.zone_label} · conseillé : ${z.cultures_conseillees.join(', ')}`;
    } catch (e) { info.textContent = '📍 Position enregistrée.'; }
  }, err => {
    info.textContent = err.code === 1 ? 'Autorisation GPS refusée : saisissez la ville à la main.' : 'Position introuvable, réessayez dehors.';
  }, { enableHighAccuracy: true, timeout: 12000 });
}

async function saveMParcelle() {
  document.querySelectorAll('.m-err').forEach(e => e.textContent='');
  const nom     = document.getElementById('d-nom').value.trim();
  const sup     = parseFloat(document.getElementById('d-sup').value);
  const statut  = document.getElementById('d-statut').value;
  const culture = document.getElementById('d-culture').value;
  const sol     = document.getElementById('d-sol').value;
  const ville   = document.getElementById('d-ville').value.trim();
  const desc    = document.getElementById('d-desc').value.trim();
  const editId  = document.getElementById('d-edit-id').value;

  let ok = true;
  if (!nom)               { document.getElementById('derr-nom').textContent     = 'Requis.'; ok=false; }
  if (!sup || sup <= 0)   { document.getElementById('derr-sup').textContent     = 'Invalide.'; ok=false; }
  if (!culture)           { document.getElementById('derr-culture').textContent = 'Requis.'; ok=false; }
  if (!sol)               { document.getElementById('derr-sol').textContent     = 'Requis.'; ok=false; }
  if (!ok) return;

  const payload = { nom, superficie: sup, culture, type_sol: sol, statut, ville: ville||null, description: desc||null, ..._gps };
  const btn = document.getElementById('d-save-btn');
  btn.disabled = true;
  btn.innerHTML = '<span class="m-spinner"></span>';

  try {
    if (editId) { await ApiParcelles.update(editId, payload); mToast('Parcelle modifiée !', 'success'); }
    else        { await ApiParcelles.create(payload);          mToast('Parcelle ajoutée !', 'success'); }
    closeDrawer();
    loadParcellesData();
  } catch(e) {
    const alert = document.getElementById('drawer-alert');
    alert.textContent    = '❌ ' + e.message;
    alert.className      = 'm-alert error';
    alert.style.display  = 'block';
  } finally {
    btn.disabled = false;
    btn.textContent = 'Enregistrer';
  }
}

function mQuickPredict(parcelleId) {
  const p = allMParcelles.find(x => x.id === parcelleId);
  if (p) {
    const sel = document.getElementById('m-sel-parcelle');
    sel.value = parcelleId;
    document.getElementById('m-culture').value    = p.culture;
    document.getElementById('m-sol').value        = p.type_sol;
    document.getElementById('m-superficie').value = p.superficie;
  }
  showPage('prediction');
}

/* ── Gestion drawer ── */
function openDrawer() {
  document.getElementById('drawer-overlay').style.display = 'block';
  document.getElementById('parcelle-drawer').style.transform = 'translateY(0)';
}
function closeDrawer() {
  document.getElementById('drawer-overlay').style.display = 'none';
  document.getElementById('parcelle-drawer').style.transform = 'translateY(100%)';
}

/* ═══════════════════════════════════════
   PAGE PRÉDICTION
═══════════════════════════════════════ */
function mPrefill() {
  const sel = document.getElementById('m-sel-parcelle');
  const opt = sel.options[sel.selectedIndex];
  if (!opt.value) return;
  document.getElementById('m-culture').value    = opt.dataset.culture || '';
  document.getElementById('m-sol').value        = opt.dataset.sol    || '';
  document.getElementById('m-superficie').value = opt.dataset.sup    || '1';
}

async function mPredict() {
  const culture   = document.getElementById('m-culture').value;
  const type_sol  = document.getElementById('m-sol').value;
  const superficie = parseFloat(document.getElementById('m-superficie').value);
  const pluv      = parseFloat(document.getElementById('m-pluv').value);
  const temp      = parseFloat(document.getElementById('m-temp').value);
  const engrais   = parseFloat(document.getElementById('m-engrais').value);

  document.querySelectorAll('.m-err').forEach(e => e.textContent='');
  let ok = true;
  if (!culture)           { document.getElementById('err-m-culture').textContent='Requis.'; ok=false; }
  if (!type_sol)          { document.getElementById('err-m-sol').textContent='Requis.';    ok=false; }
  if (!superficie||superficie<=0){ document.getElementById('err-m-sup').textContent='Invalide.'; ok=false; }
  if (!ok) return;

  const btn = document.getElementById('m-btn-predict');
  btn.disabled = true;
  btn.innerHTML = '<span class="m-spinner"></span> Calcul en cours…';

  try {
    const selP = document.getElementById('m-sel-parcelle');
    const optP = selP.options[selP.selectedIndex];
    const res = await ApiPrediction.predict({
      culture, type_sol, superficie, pluviometrie: pluv, temperature: temp, engrais_kg: engrais,
      parcelle_id: selP.value ? parseInt(selP.value) : null,
      ville: (optP && optP.dataset.ville) || null,
    });
    if (res.avertissement) showToast(res.avertissement, 'warning', 7000);

    const card = document.getElementById('pred-result-card');
    card.style.display = 'block';
    card.scrollIntoView({ behavior: 'smooth' });

    const icons = {cacao:'🍫',cafe:'☕',hevea:'🌳',palmier:'🌴',anacarde:'🥜',coton:'☁️',mais:'🌽',riz:'🌾',manioc:'🥔',igname:'🍠',arachide:'🥜',sorgho:'🌿',mil:'🌿'};
    document.getElementById('prc-value').textContent   = res.rendement_predit.toFixed(2);
    document.getElementById('prc-culture').textContent = `${icons[culture]||'🌱'} ${culture} · ${superficie} ha`;

    const conf = res.confiance || 80;
    document.getElementById('prc-conf-val').textContent = conf.toFixed(0) + '%';
    setTimeout(() => { document.getElementById('prc-conf-fill').style.width = conf + '%'; }, 100);

    // Conseils
    let tips = [];
    if (pluv < 400)  tips.push('💧 Pluviométrie faible — pensez à l\'irrigation');
    if (temp > 35)   tips.push('🌡️ Température élevée — arrosez le matin');
    if (engrais < 20) tips.push('🌿 Augmentez l\'apport d\'engrais');
    if (res.rendement_predit > 4) tips.push('✅ Excellent rendement prévu !');
    document.getElementById('prc-tips').innerHTML = tips.map(t => `<div style="margin-top:5px;">${t}</div>`).join('');

    mToast('Prédiction effectuée !', 'success');
    loadPredHistory();
  } catch(e) {
    mToast('Erreur : ' + e.message, 'error');
  } finally {
    btn.disabled = false;
    btn.innerHTML = '🔮 Lancer la prédiction';
  }
}

async function loadPredHistory() {
  try {
    const list = await ApiPrediction.historique();
    const icons = {cacao:'🍫',cafe:'☕',hevea:'🌳',palmier:'🌴',anacarde:'🥜',coton:'☁️',mais:'🌽',riz:'🌾',manioc:'🥔',igname:'🍠',arachide:'🥜',sorgho:'🌿',mil:'🌿'};
    const container = document.getElementById('m-pred-history');
    if (list.length === 0) {
      container.innerHTML = '<p style="color:var(--gray400);font-size:.82rem;text-align:center;padding:10px 0;">Aucune prédiction encore</p>';
      return;
    }
    container.innerHTML = list.slice(0,5).map(p => `
      <div class="m-pred-item">
        <div class="mpi-left">
          <div class="mpi-name">${icons[p.culture]||'🌱'} ${p.culture} · ${p.superficie} ha</div>
          <div class="mpi-date">${formatDateShort(p.created_at)}</div>
        </div>
        <div class="mpi-right">${p.rendement_predit.toFixed(2)} t/ha</div>
      </div>`).join('');
  } catch(e) {}
}

/* ═══════════════════════════════════════
   PAGE AGRIBOT
═══════════════════════════════════════ */
const mUser = () => Auth.getUser();
let mMsgCount = 0;

function mRenderMessage(role, content, time = null) {
  const container = document.getElementById('m-chat-messages');
  const user      = mUser();
  const initials  = role === 'user'
    ? ((user?.firstname?.[0]||'')+(user?.lastname?.[0]||'')).toUpperCase()||'U'
    : '🤖';

  const timeStr = time
    ? new Date(time).toLocaleTimeString('fr-FR',{hour:'2-digit',minute:'2-digit'})
    : new Date().toLocaleTimeString('fr-FR',{hour:'2-digit',minute:'2-digit'});

  const html = role === 'assistant' ? markdownToHtml(content) : escHtml(content);

  const row = document.createElement('div');
  row.className = `m-msg-row ${role === 'user' ? 'user' : 'bot'}`;
  row.innerHTML = `
    <div class="m-msg-av ${role === 'user' ? 'user' : 'bot'}">${initials}</div>
    <div>
      <div class="m-bubble ${role === 'user' ? 'user' : 'bot'}">${html}</div>
      <div class="m-bubble-time">${timeStr}</div>
    </div>`;
  container.appendChild(row);
  container.scrollTop = container.scrollHeight;
}

function escHtml(s) {
  return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}

function mShowTyping() {
  const c = document.getElementById('m-chat-messages');
  const d = document.createElement('div');
  d.className = 'm-msg-row bot'; d.id = 'm-typing';
  d.innerHTML = `<div class="m-msg-av bot">🤖</div>
    <div class="m-bubble bot"><div class="m-typing">
      <div class="m-tdot"></div><div class="m-tdot"></div><div class="m-tdot"></div>
    </div></div>`;
  c.appendChild(d);
  c.scrollTop = c.scrollHeight;
}
function mHideTyping() { document.getElementById('m-typing')?.remove(); }

async function mSend() {
  const input = document.getElementById('m-chat-input');
  const text  = input.value.trim();
  if (!text) return;
  input.value = ''; input.style.height = 'auto';

  mRenderMessage('user', text);
  mMsgCount++;

  const btn = document.getElementById('m-send-btn');
  btn.disabled = true;
  mShowTyping();

  try {
    const res = await ApiAgribot.sendMessage(text);
    mHideTyping();
    mRenderMessage('assistant', res.content, res.created_at);
  } catch(e) {
    mHideTyping();
    mRenderMessage('assistant', '❌ Erreur : ' + e.message);
  } finally {
    btn.disabled = false;
  }
}

function mSuggest(text) {
  document.getElementById('m-chat-input').value = text;
  mSend();
}

async function mClearChat() {
  if (!confirm('Effacer toute la conversation ?')) return;
  try {
    await ApiAgribot.clearHistory();
    document.getElementById('m-chat-messages').innerHTML = '';
    mWelcome();
    mToast('Conversation effacée', 'success');
  } catch(e) { mToast('Erreur', 'error'); }
}

async function loadChatHistory() {
  try {
    const history = await ApiAgribot.historique();
    if (history.length === 0) { mWelcome(); return; }
    history.forEach(m => mRenderMessage(m.role === 'user' ? 'user' : 'assistant', m.content, m.created_at));
  } catch(e) { mWelcome(); }
}

function mWelcome() {
  const name = mUser()?.firstname || 'agriculteur';
  mRenderMessage('assistant',
    `👋 Bonjour **${name}** ! Je suis AgriBot.\n\nPosez-moi vos questions sur vos cultures, le sol, la météo ou les maladies.`
  );
}

function mAutoResize(el) {
  el.style.height = 'auto';
  el.style.height = Math.min(el.scrollHeight, 100) + 'px';
}

/* ═══════════════════════════════════════
   PAGE MÉTÉO
═══════════════════════════════════════ */
async function loadMMeteo(ville, btn) {
  // Mettre à jour chips
  if (btn) {
    document.querySelectorAll('#page-meteo .chip').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
  }

  const hero = document.getElementById('m-meteo-hero');
  hero.innerHTML = '<div class="mhc-loading">Chargement…</div>';

  try {
    const [current, previsions] = await Promise.all([
      ApiMeteo.current(ville),
      ApiMeteo.previsions(ville),
    ]);

    // Hero
    hero.innerHTML = `
      <div class="mhc-city">📍 ${current.ville}</div>
      <div class="mhc-main">
        <div class="mhc-icon">${meteoIcon(current.icone)}</div>
        <div class="mhc-temp">${current.temperature}°C</div>
        <div class="mhc-info">
          <div class="mhc-desc">${current.description}</div>
          <div class="mhc-feel">Ressenti ${current.ressenti}°C</div>
        </div>
      </div>
      <div class="mhc-details">
        <div class="mhc-detail">💧 ${current.humidite}%</div>
        <div class="mhc-detail">🌬️ ${current.vent} km/h</div>
        <div class="mhc-detail">📊 ${current.pression} hPa</div>
      </div>`;

    // Prévisions
    const prevList = document.getElementById('m-prev-list');
    prevList.innerHTML = previsions.previsions.map((d, i) => `
      <div class="m-prev-item ${i===0?'today':''}">
        <span class="mpi-day">${d.label}</span>
        <span class="mpi-icon">${meteoIcon(d.icone)}</span>
        <span class="mpi-temp">${d.temp}°C</span>
        <span class="mpi-rain">💧 ${d.pluie} mm</span>
      </div>`).join('');

    // Conseils agro
    const totalPluie = previsions.previsions.slice(0,3).reduce((s,d)=>s+d.pluie,0);
    const tips = [];
    if (current.temperature > 35) tips.push({icon:'🌡️',title:'Chaleur intense',text:`${current.temperature}°C — arrosez tôt le matin.`});
    else tips.push({icon:'🌡️',title:'Température favorable',text:`${current.temperature}°C — conditions idéales.`});
    if (totalPluie > 50) tips.push({icon:'🌧️',title:'Fortes pluies prévues',text:`${totalPluie.toFixed(0)} mm sur 3 jours — vérifiez le drainage.`});
    else if (totalPluie < 10) tips.push({icon:'☀️',title:'Temps sec',text:`Peu de pluie — programmez une irrigation.`});
    else tips.push({icon:'🌦️',title:'Pluies modérées',text:`${totalPluie.toFixed(0)} mm prévus — bonnes conditions.`});
    if (current.humidite > 75) tips.push({icon:'🦠',title:'Humidité élevée',text:'Risque de maladies fongiques augmenté.'});

    document.getElementById('m-agro-tips').innerHTML = tips.map(t => `
      <div class="m-agro-tip">
        <div class="mat-icon">${t.icon}</div>
        <div class="mat-body"><h4>${t.title}</h4><p>${t.text}</p></div>
      </div>`).join('');

  } catch(e) {
    hero.innerHTML = '<div class="mhc-loading" style="color:var(--red);">Météo indisponible</div>';
  }
}

function mLoadVille(ville, btn) {
  if (!ville) return;
  loadMMeteo(ville, btn);
}

/* ═══════════════════════════════════════
   PAGE PROFIL
═══════════════════════════════════════ */
async function loadProfil() {
  try {
    const [parcelles, preds, msgs] = await Promise.all([
      ApiParcelles.list(),
      ApiPrediction.historique(),
      ApiAgribot.historique(),
    ]);
    document.getElementById('ps-parcelles').textContent = parcelles.length;
    document.getElementById('ps-preds').textContent     = preds.length;
    document.getElementById('ps-msgs').textContent      = msgs.filter(m=>m.role==='user').length;
  } catch(e) {}
}

function switchToWeb() {
  window.location.href = '../app/pages/dashboard.html';
}

function mLogout() {
  if (confirm('Se déconnecter ?')) Auth.logout();
}

/* ═══════════════════════════════════════
   UTILITAIRES
═══════════════════════════════════════ */
function mToast(msg, type = 'success') {
  let container = document.getElementById('m-toast-container');
  const t = document.createElement('div');
  t.className = `m-toast ${type}`;
  t.textContent = msg;
  container.appendChild(t);
  setTimeout(() => { t.style.opacity='0'; t.style.transition='opacity .3s'; setTimeout(()=>t.remove(),300); }, 2500);
}
