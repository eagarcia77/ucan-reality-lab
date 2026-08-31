(() => {
  'use strict';
  const $ = id => document.getElementById(id);
  const isLocal = ['localhost','127.0.0.1'].includes(location.hostname);
  const API = isLocal ? '/api' : 'https://ucan-reality-lab.onrender.com/api';
  let token = localStorage.getItem('ucan_access_token') || '';
  let currentUser = null;
  let projectCache = [];
  const headers = (extra = {}) => ({ ...extra, Authorization: `Bearer ${token}` });
  const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const wait = ms => new Promise(resolve => setTimeout(resolve, ms));

  function showPanel(name) {
    ['loginPanel','registerPanel','forgotPanel'].forEach(id => $(id).classList.toggle('hidden', id !== name));
  }
  function showLogin(message = '', clearSession = false) {
    if (clearSession) {
      token = '';
      currentUser = null;
      localStorage.removeItem('ucan_access_token');
    }
    $('authView').classList.remove('hidden');
    $('dashboardView').classList.add('hidden');
    $('sessionArea').classList.add('hidden');
    showPanel('loginPanel');
    $('loginMessage').textContent = message;
  }
  function ensureProjectSearch() {
    if ($('projectSearch')) return;
    const input = document.createElement('input');
    input.id = 'projectSearch';
    input.type = 'search';
    input.placeholder = 'Buscar por proyecto, curso, nivel o creador';
    input.setAttribute('aria-label', 'Buscar proyectos');
    input.addEventListener('input', renderProjects);
    $('projects').before(input);
  }
  function ensureAdminLink(user) {
    let a = $('adminUsersLink');
    if (user.role === 'admin' && !a) {
      a = document.createElement('a');
      a.id = 'adminUsersLink';
      a.className = 'btn secondary';
      a.href = '/admin-users.html';
      a.textContent = 'Administrar cuentas';
      const session = $('sessionArea');
      const logout = $('logoutButton');
      session.insertBefore(a, logout || null);
    }
    if (a) a.classList.toggle('hidden', user.role !== 'admin');
  }
  function showDashboard(user) {
    currentUser = user;
    $('authView').classList.add('hidden');
    $('dashboardView').classList.remove('hidden');
    $('sessionArea').classList.remove('hidden');
    $('userBadge').textContent = `${user.full_name} · ${user.role}`;
    $('projectForm').classList.toggle('hidden', user.role === 'reviewer');
    const heading = $('projectsHeading');
    if (heading) heading.textContent = user.role === 'admin' ? 'Todos los proyectos' : 'Mis proyectos';
    ensureAdminLink(user);
    ensureProjectSearch();
  }
  async function parse(response) {
    const body = await response.json().catch(() => ({}));
    if (!response.ok) {
      const error = new Error(body.detail || `Error ${response.status}`);
      error.status = response.status;
      throw error;
    }
    return body;
  }
  async function fetchTimed(url, options = {}, timeoutMs = 70000) {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), timeoutMs);
    try {
      return await fetch(url, { ...options, signal: controller.signal });
    } catch (error) {
      if (error?.name === 'AbortError') {
        const e = new Error('El servidor tardó demasiado en responder.');
        e.code = 'TIMEOUT';
        throw e;
      }
      throw error;
    } finally {
      clearTimeout(timeout);
    }
  }
  async function fetchWithRetry(url, options = {}, attempts = 2, timeoutMs = 70000) {
    let last;
    for (let i = 0; i < attempts; i++) {
      try {
        return await fetchTimed(url, options, timeoutMs);
      } catch (e) {
        last = e;
        if (i < attempts - 1) await wait(1800);
      }
    }
    throw last || new Error('No fue posible conectar con el servidor.');
  }
  async function deleteProject(projectId, projectTitle, button) {
    if (!window.confirm(`¿Desea borrar permanentemente el proyecto “${projectTitle}”?\n\nTambién se eliminarán la actividad, la rúbrica y la configuración guardada. Esta acción no se puede deshacer.`)) return;
    button.disabled = true;
    button.textContent = 'Borrando…';
    try {
      const response = await fetchWithRetry(`${API}/projects/${encodeURIComponent(projectId)}`, { method:'DELETE', headers:headers() }, 2, 45000);
      if (response.status !== 204) await parse(response);
      localStorage.removeItem(`ucan_v8_${projectId}`);
      localStorage.removeItem(`ucan_authoring_${projectId}`);
      await loadProjects();
    } catch (error) {
      button.disabled = false;
      button.textContent = 'Borrar proyecto';
      window.alert(`No fue posible borrar el proyecto: ${error.message}`);
    }
  }
  function renderProjects() {
    const q = ($('projectSearch')?.value || '').trim().toLowerCase();
    const ps = projectCache.filter(p => [p.title,p.description,p.course,p.academic_level,p.owner_name,p.owner_email].join(' ').toLowerCase().includes(q));
    if (!ps.length) {
      $('projects').innerHTML = `<p class="muted">${q ? 'No se encontraron proyectos.' : 'Todavía no hay proyectos.'}</p>`;
      return;
    }
    $('projects').innerHTML = ps.map(p => {
      const ownerName = p.owner_name || currentUser?.full_name || 'Usuario';
      const ownerEmail = p.owner_email || currentUser?.email || '';
      return `<article class="project"><h3>${esc(p.title)}</h3><p class="project-owner"><strong>Creado por:</strong> ${esc(ownerName)}${ownerEmail ? ` · ${esc(ownerEmail)}` : ''}</p><p>${esc(p.description || 'Sin descripción')}</p><p class="muted">${esc(p.course || 'Curso no especificado')} · ${esc(p.academic_level)} · versión ${p.version}</p><div><a class="btn" href="/authoring-v8.html?project=${encodeURIComponent(p.id)}&title=${encodeURIComponent(p.title)}&course=${encodeURIComponent(p.course || '')}&level=${encodeURIComponent(p.academic_level || '')}">Abrir Studio v10.4</a><button type="button" class="secondary delete-project" data-project-id="${esc(p.id)}" data-project-title="${esc(p.title)}">Borrar proyecto</button></div></article>`;
    }).join('');
    document.querySelectorAll('.delete-project').forEach(button => button.addEventListener('click', () => deleteProject(button.dataset.projectId, button.dataset.projectTitle, button)));
  }
  async function loadProjects() {
    $('projects').textContent = 'Cargando proyectos…';
    try {
      const endpoint = currentUser?.role === 'admin' ? `${API}/admin/projects` : `${API}/projects`;
      projectCache = await parse(await fetchWithRetry(endpoint, { headers:headers() }, 2, 45000));
      renderProjects();
    } catch (e) {
      if (e.status === 401) showLogin('La sesión expiró. Inicie sesión nuevamente.', true);
      else $('projects').innerHTML = `<p class="error">No se pudieron cargar los proyectos: ${esc(e.message || 'servidor no disponible')}</p><button id="retryProjects" class="secondary">Intentar nuevamente</button>`;
      $('retryProjects')?.addEventListener('click', loadProjects);
    }
  }
  async function verify() {
    if (!token) return showLogin();
    $('loginMessage').textContent = 'Recuperando su sesión…';
    try {
      const user = await parse(await fetchWithRetry(`${API}/auth/me`, { headers:headers() }, 1, 45000));
      showDashboard(user);
      loadProjects();
    } catch (e) {
      if (e.status === 401 || e.status === 403) showLogin('La sesión expiró. Inicie sesión nuevamente.', true);
      else showLogin('El servidor está iniciando. Su sesión se conserva; puede intentar entrar nuevamente.', false);
    }
  }

  $('loginTab').onclick = () => showPanel('loginPanel');
  $('registerTab').onclick = () => showPanel('registerPanel');
  $('forgotButton').onclick = () => { $('forgotEmail').value = $('email').value; showPanel('forgotPanel'); $('forgotMessage').textContent = ''; };
  $('backLogin').onclick = () => showPanel('loginPanel');
  $('logoutButton').onclick = () => showLogin('Sesión cerrada.', true);
  $('refreshButton').onclick = loadProjects;

  $('loginForm').onsubmit = async e => {
    e.preventDefault();
    const m = $('loginMessage');
    const submit = e.submitter || e.target.querySelector('button[type="submit"]');
    if (submit) submit.disabled = true;
    m.className = '';
    m.textContent = 'Conectando con el servidor y validando sus credenciales…';
    try {
      const response = await fetchWithRetry(`${API}/auth/login`, {
        method:'POST', headers:{'Content-Type':'application/json'},
        body:JSON.stringify({ email:$('email').value.trim(), password:$('password').value })
      }, 2, 70000);
      const b = await parse(response);
      token = b.access_token;
      localStorage.setItem('ucan_access_token', token);
      m.className = 'success';
      m.textContent = 'Acceso correcto.';
      showDashboard(b.user);
      loadProjects();
    } catch (err) {
      m.className = 'error';
      if (err?.status === 401 || err?.status === 422) m.textContent = err.message;
      else if (err?.code === 'TIMEOUT') m.textContent = 'Render está tardando en iniciar. Espere 20 segundos y presione Entrar nuevamente.';
      else m.textContent = `No fue posible conectar con el servidor: ${err.message || 'error de conexión'}.`;
    } finally {
      if (submit) submit.disabled = false;
    }
  };

  $('registerForm').onsubmit = async e => {
    e.preventDefault();
    const m = $('registerMessage');
    const submit = e.submitter || e.target.querySelector('button[type="submit"]');
    if (submit) submit.disabled = true;
    m.className = '';
    m.textContent = 'Creando cuenta…';
    if ($('registerPassword').value !== $('registerPasswordConfirm').value) {
      m.className = 'error'; m.textContent = 'Las contraseñas no coinciden.'; if (submit) submit.disabled = false; return;
    }
    try {
      const b = await parse(await fetchWithRetry(`${API}/auth/register`, {
        method:'POST', headers:{'Content-Type':'application/json'},
        body:JSON.stringify({ full_name:$('registerName').value, email:$('registerEmail').value.trim(), password:$('registerPassword').value })
      }, 2, 70000));
      token = b.access_token;
      localStorage.setItem('ucan_access_token', token);
      showDashboard(b.user);
      loadProjects();
    } catch (err) {
      m.className = 'error';
      m.textContent = err.message || 'No se pudo crear la cuenta.';
      if (/ya existe/i.test(err.message || '')) $('forgotEmail').value = $('registerEmail').value.trim();
    } finally {
      if (submit) submit.disabled = false;
    }
  };

  $('forgotForm').onsubmit = async e => {
    e.preventDefault();
    const m = $('forgotMessage');
    const submit = e.submitter || e.target.querySelector('button[type="submit"]');
    if (submit) submit.disabled = true;
    m.className = '';
    m.textContent = 'Solicitando el enlace de recuperación…';
    try {
      const b = await parse(await fetchWithRetry(`${API}/auth/forgot-password`, {
        method:'POST', headers:{'Content-Type':'application/json'},
        body:JSON.stringify({ email:$('forgotEmail').value.trim() })
      }, 2, 70000));
      m.className = 'success';
      m.textContent = b.message + (b.email_delivery_configured ? '' : ' El servicio de correo todavía no está configurado en Render.');
    } catch (err) {
      m.className = 'error';
      m.textContent = err?.code === 'TIMEOUT' ? 'El servidor está tardando en iniciar. Espere 20 segundos y vuelva a intentarlo.' : (err.message || 'No se pudo procesar la solicitud.');
    } finally {
      if (submit) submit.disabled = false;
    }
  };

  $('projectForm').onsubmit = async e => {
    e.preventDefault();
    const m = $('formMessage');
    m.textContent = 'Creando…';
    try {
      const p = await parse(await fetchWithRetry(`${API}/projects`, {
        method:'POST', headers:headers({'Content-Type':'application/json'}),
        body:JSON.stringify({ title:$('title').value, course:$('course').value, academic_level:$('level').value, description:$('description').value })
      }, 2, 45000));
      e.target.reset();
      location.href = `/authoring-v8.html?project=${encodeURIComponent(p.id)}&title=${encodeURIComponent(p.title)}&course=${encodeURIComponent(p.course || '')}&level=${encodeURIComponent(p.academic_level || '')}`;
    } catch (err) {
      m.className = 'error';
      m.textContent = err.message || 'No se pudo crear el proyecto.';
    }
  };

  fetchWithRetry(`${API}/auth/registration-config`, {}, 1, 30000).then(parse).then(c => {
    $('domainHelp').textContent = `Dominios permitidos: ${c.allowed_domains.map(d => '@' + d).join(', ')}`;
  }).catch(() => { $('domainHelp').textContent = 'Utilice únicamente su correo institucional de la Universidad Interamericana.'; });

  verify();
})();