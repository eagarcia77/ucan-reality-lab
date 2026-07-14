(() => {
  const $ = id => document.getElementById(id);
  const API = location.hostname.endsWith('onrender.com') ? 'https://ucan-reality-lab.onrender.com/api' : '/api';
  let token = localStorage.getItem('ucan_access_token') || '';
  const headers = (extra = {}) => ({ ...extra, Authorization: `Bearer ${token}` });
  const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  function showPanel(name) { ['loginPanel','registerPanel','forgotPanel'].forEach(id => $(id).classList.toggle('hidden', id !== name)); }
  function showLogin(message = '') { token=''; localStorage.removeItem('ucan_access_token'); $('authView').classList.remove('hidden'); $('dashboardView').classList.add('hidden'); $('sessionArea').classList.add('hidden'); showPanel('loginPanel'); $('loginMessage').textContent=message; }
  function showDashboard(user) { $('authView').classList.add('hidden'); $('dashboardView').classList.remove('hidden'); $('sessionArea').classList.remove('hidden'); $('userBadge').textContent=`${user.full_name} · ${user.role}`; $('projectForm').classList.toggle('hidden',user.role==='reviewer'); let a=document.getElementById('adminUsersLink'); if(user.role==='admin'&&!a){a=document.createElement('a');a.id='adminUsersLink';a.className='btn secondary';a.href='/admin-users.html';a.textContent='Administrar cuentas';$('sessionArea').insertBefore(a,$('logoutButton'));} if(a)a.classList.toggle('hidden',user.role!=='admin'); }
  async function json(response){const body=await response.json().catch(()=>({}));if(!response.ok)throw new Error(body.detail||`Error ${response.status}`);return body;}
  async function deleteProject(projectId, projectTitle, button){
    const confirmed = window.confirm(`¿Desea borrar permanentemente el proyecto “${projectTitle}”?\n\nTambién se eliminarán la actividad, la rúbrica y la configuración guardada. Esta acción no se puede deshacer.`);
    if(!confirmed) return;
    button.disabled = true;
    button.textContent = 'Borrando…';
    try {
      const response = await fetch(`${API}/projects/${encodeURIComponent(projectId)}`, { method:'DELETE', headers:headers() });
      if(response.status !== 204) await json(response);
      localStorage.removeItem(`ucan_v8_${projectId}`);
      localStorage.removeItem(`ucan_authoring_${projectId}`);
      await loadProjects();
    } catch(error) {
      button.disabled = false;
      button.textContent = 'Borrar proyecto';
      window.alert(`No fue posible borrar el proyecto: ${error.message}`);
    }
  }
  async function loadProjects(){
    $('projects').textContent='Cargando proyectos…';
    try{
      const ps=await json(await fetch(`${API}/projects`,{headers:headers()}));
      if(!ps.length){$('projects').innerHTML='<p class="muted">Todavía no hay proyectos.</p>';return}
      $('projects').innerHTML=ps.map(p=>`<article class="project" data-project-id="${esc(p.id)}"><h3>${esc(p.title)}</h3><p>${esc(p.description||'Sin descripción')}</p><p class="muted">${esc(p.course||'Curso no especificado')} · ${esc(p.academic_level)} · versión ${p.version}</p><div><a class="btn" href="/authoring-v8.html?project=${encodeURIComponent(p.id)}&title=${encodeURIComponent(p.title)}&course=${encodeURIComponent(p.course||'')}&level=${encodeURIComponent(p.academic_level||'')}">Abrir Studio v8.1 LTS</a><button type="button" class="secondary delete-project" data-project-id="${esc(p.id)}" data-project-title="${esc(p.title)}">Borrar proyecto</button></div></article>`).join('');
      document.querySelectorAll('.delete-project').forEach(button=>{
        button.addEventListener('click',()=>deleteProject(button.dataset.projectId,button.dataset.projectTitle,button));
      });
    }catch(e){if(/sesión|401/i.test(e.message))showLogin('La sesión expiró.');else $('projects').innerHTML=`<p class="error">${esc(e.message)}</p>`;}
  }
  async function verify(){if(!token)return showLogin();try{const user=await json(await fetch(`${API}/auth/me`,{headers:headers()}));showDashboard(user);loadProjects()}catch{showLogin('La sesión expiró. Inicie sesión nuevamente.')}}
  $('loginTab').onclick=()=>showPanel('loginPanel'); $('registerTab').onclick=()=>showPanel('registerPanel'); $('forgotButton').onclick=()=>{$('forgotEmail').value=$('email').value;showPanel('forgotPanel')}; $('backLogin').onclick=()=>showPanel('loginPanel'); $('logoutButton').onclick=()=>showLogin('Sesión cerrada.'); $('refreshButton').onclick=loadProjects;
  $('loginForm').onsubmit=async e=>{e.preventDefault();const m=$('loginMessage');m.className='';m.textContent='Validando…';try{const b=await json(await fetch(`${API}/auth/login`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({email:$('email').value.trim(),password:$('password').value})}));token=b.access_token;localStorage.setItem('ucan_access_token',token);showDashboard(b.user);loadProjects()}catch(err){m.className='error';m.textContent=err.message}};
  $('registerForm').onsubmit=async e=>{e.preventDefault();const m=$('registerMessage');m.className='';m.textContent='Creando cuenta…';if($('registerPassword').value!==$('registerPasswordConfirm').value){m.className='error';m.textContent='Las contraseñas no coinciden.';return}try{const b=await json(await fetch(`${API}/auth/register`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({full_name:$('registerName').value,email:$('registerEmail').value.trim(),password:$('registerPassword').value})}));token=b.access_token;localStorage.setItem('ucan_access_token',token);showDashboard(b.user);loadProjects()}catch(err){m.className='error';m.textContent=err.message;if(/ya existe/i.test(err.message)){$('forgotEmail').value=$('registerEmail').value.trim();}}};
  $('forgotForm').onsubmit=async e=>{e.preventDefault();const m=$('forgotMessage');m.textContent='Procesando…';try{const b=await json(await fetch(`${API}/auth/forgot-password`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({email:$('forgotEmail').value.trim()})}));m.className='success';m.textContent=b.message+(b.email_delivery_configured?'':' El correo saliente todavía no está configurado.')}catch(err){m.className='error';m.textContent=err.message}};
  $('projectForm').onsubmit=async e=>{e.preventDefault();const m=$('formMessage');m.textContent='Creando…';try{const p=await json(await fetch(`${API}/projects`,{method:'POST',headers:headers({'Content-Type':'application/json'}),body:JSON.stringify({title:$('title').value,course:$('course').value,academic_level:$('level').value,description:$('description').value})}));e.target.reset();location.href=`/authoring-v8.html?project=${encodeURIComponent(p.id)}&title=${encodeURIComponent(p.title)}&course=${encodeURIComponent(p.course||'')}&level=${encodeURIComponent(p.academic_level||'')}`;}catch(err){m.className='error';m.textContent=err.message}};
  fetch(`${API}/auth/registration-config`).then(json).then(c=>$('domainHelp').textContent=`Dominios permitidos: ${c.allowed_domains.map(d=>'@'+d).join(', ')}`).catch(()=>{});verify();
})();