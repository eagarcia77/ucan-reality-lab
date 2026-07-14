(() => {
  const $ = id => document.getElementById(id);
  const API = location.hostname.endsWith('onrender.com') ? 'https://ucan-reality-lab.onrender.com/api' : '/api';
  let token = localStorage.getItem('ucan_access_token') || '';
  const headers = (extra = {}) => ({ ...extra, Authorization: `Bearer ${token}` });
  const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));

  function showPanel(name) {
    ['loginPanel','registerPanel','forgotPanel'].forEach(id => $(id).classList.toggle('hidden', id !== name));
  }
  function showLogin(message = '') {
    token = ''; localStorage.removeItem('ucan_access_token');
    $('authView').classList.remove('hidden'); $('dashboardView').classList.add('hidden'); $('sessionArea').classList.add('hidden');
    showPanel('loginPanel'); $('loginMessage').textContent = message;
  }
  function showDashboard(user) {
    $('authView').classList.add('hidden'); $('dashboardView').classList.remove('hidden'); $('sessionArea').classList.remove('hidden');
    $('userBadge').textContent = `${user.full_name} · ${user.role}`;
    $('projectForm').classList.toggle('hidden', user.role === 'reviewer');
  }
  async function json(response) { const body = await response.json().catch(() => ({})); if (!response.ok) throw new Error(body.detail || 'Ocurrió un error.'); return body; }
  async function loadProjects() {
    $('projects').textContent = 'Cargando proyectos…';
    try {
      const projects = await json(await fetch(`${API}/projects`, { headers: headers() }));
      if (!projects.length) { $('projects').innerHTML = '<p class="muted">Todavía no hay proyectos.</p>'; return; }
      $('projects').innerHTML = projects.map(p => `<article class="project"><h3>${esc(p.title)}</h3><p>${esc(p.description || 'Sin descripción')}</p><p class="muted">${esc(p.course || 'Curso no especificado')} · ${esc(p.academic_level)} · versión ${p.version}</p><a class="btn" href="/authoring.html?project=${encodeURIComponent(p.id)}&title=${encodeURIComponent(p.title)}&course=${encodeURIComponent(p.course || '')}&level=${encodeURIComponent(p.academic_level || '')}">Abrir Studio Guiado v7.7</a></article>`).join('');
    } catch (e) { if (/sesión|401/i.test(e.message)) showLogin('La sesión expiró.'); else $('projects').innerHTML = `<p class="error">${esc(e.message)}</p>`; }
  }
  async function verify() {
    if (!token) return showLogin();
    try { const user = await json(await fetch(`${API}/auth/me`, { headers: headers() })); showDashboard(user); loadProjects(); }
    catch { showLogin('La sesión expiró.'); }
  }

  $('loginTab').onclick = () => showPanel('loginPanel');
  $('registerTab').onclick = () => showPanel('registerPanel');
  $('forgotButton').onclick = () => { $('forgotEmail').value = $('email').value; showPanel('forgotPanel'); };
  $('backLogin').onclick = () => showPanel('loginPanel');
  $('logoutButton').onclick = () => showLogin('Sesión cerrada.');
  $('refreshButton').onclick = loadProjects;

  $('loginForm').onsubmit = async e => { e.preventDefault(); $('loginMessage').textContent = 'Validando…'; try { const body = await json(await fetch(`${API}/auth/login`, { method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({email:$('email').value,password:$('password').value}) })); token = body.access_token; localStorage.setItem('ucan_access_token', token); showDashboard(body.user); loadProjects(); } catch (err) { $('loginMessage').className='error'; $('loginMessage').textContent=err.message; } };
  $('registerForm').onsubmit = async e => { e.preventDefault(); const m=$('registerMessage'); if ($('registerPassword').value !== $('registerPasswordConfirm').value) { m.className='error'; m.textContent='Las contraseñas no coinciden.'; return; } try { const body=await json(await fetch(`${API}/auth/register`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({full_name:$('registerName').value,email:$('registerEmail').value,password:$('registerPassword').value})})); token=body.access_token;localStorage.setItem('ucan_access_token',token);showDashboard(body.user);loadProjects(); } catch(err){m.className='error';m.textContent=err.message;} };
  $('forgotForm').onsubmit = async e => { e.preventDefault(); const m=$('forgotMessage'); m.className='';m.textContent='Procesando…'; try { const body=await json(await fetch(`${API}/auth/forgot-password`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({email:$('forgotEmail').value})})); m.className='success';m.textContent=body.message + (body.email_delivery_configured ? '' : ' El administrador todavía debe configurar el correo saliente del sistema.'); } catch(err){m.className='error';m.textContent=err.message;} };
  $('projectForm').onsubmit = async e => { e.preventDefault(); const m=$('formMessage');m.textContent='Creando…'; try { await json(await fetch(`${API}/projects`,{method:'POST',headers:headers({'Content-Type':'application/json'}),body:JSON.stringify({title:$('title').value,course:$('course').value,academic_level:$('level').value,description:$('description').value})})); e.target.reset();m.className='success';m.textContent='Proyecto creado. Ábralo para comenzar.';loadProjects(); } catch(err){m.className='error';m.textContent=err.message;} };
  fetch(`${API}/auth/registration-config`).then(json).then(c => $('domainHelp').textContent=`Dominios permitidos: ${c.allowed_domains.map(d=>'@'+d).join(', ')}`).catch(()=>{});
  verify();
})();