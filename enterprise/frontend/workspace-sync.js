(() => {
  const params = new URLSearchParams(location.search);
  const projectId = params.get('project');
  if (!projectId) return;
  const API = location.hostname.endsWith('onrender.com') ? 'https://ucan-reality-lab.onrender.com/api' : '/api';
  const token = () => localStorage.getItem('ucan_access_token') || '';
  let uploadedImageData = '';
  let syncTimer;

  const originalData = typeof window.data === 'function' ? window.data : null;
  if (originalData) {
    window.data = function () {
      return { ...originalData(), uploadedImageData };
    };
  }

  const originalLearnerHtml = typeof window.learnerHtml === 'function' ? window.learnerHtml : null;
  if (originalLearnerHtml) {
    window.learnerHtml = function (d, standard = 'web') {
      let html = originalLearnerHtml(d, standard);
      const image = d.uploadedImageData || uploadedImageData;
      if (image && /^data:image\//.test(image)) {
        const block = `<h2>Imagen de referencia</h2><img src="${image}" alt="Imagen educativa cargada por el profesor" style="display:block;max-width:100%;height:auto;margin:1rem auto">`;
        html = html.replace('<h2>Objetivos</h2>', `${block}<h2>Objetivos</h2>`);
      }
      return html;
    };
  }

  async function readImage(file) {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = () => resolve(String(reader.result || ''));
      reader.onerror = () => reject(new Error('No fue posible leer la imagen.'));
      reader.readAsDataURL(file);
    });
  }

  document.getElementById('resourceFile')?.addEventListener('change', async event => {
    const file = event.target.files?.[0];
    if (file?.type.startsWith('image/')) uploadedImageData = await readImage(file);
    scheduleSync();
  });

  async function loadWorkspace() {
    if (!token()) return;
    try {
      const response = await fetch(`${API}/projects/${projectId}/workspace`, { headers: { Authorization: `Bearer ${token()}` } });
      if (!response.ok) return;
      const body = await response.json();
      const remote = body.content || {};
      uploadedImageData = remote.uploadedImageData || '';
      if (!Object.keys(remote).length || typeof window.load !== 'function') return;
      localStorage.setItem(`ucan_authoring_${projectId}`, JSON.stringify(remote));
      const rubric = document.getElementById('rubric');
      if (rubric) rubric.innerHTML = '';
      window.load();
      document.getElementById('autosave').textContent = 'Sincronizado ✓';
    } catch (_) {}
  }

  async function syncWorkspace() {
    if (!token() || typeof window.data !== 'function') return;
    try {
      const content = window.data();
      const score = Number((document.getElementById('qualityScore')?.textContent || '0').split('/')[0]) || 0;
      const response = await fetch(`${API}/projects/${projectId}/workspace`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token()}` },
        body: JSON.stringify({ content, quality_score: score })
      });
      if (!response.ok) throw new Error();
      document.getElementById('autosave').textContent = 'Guardado en la nube ✓';
    } catch (_) {
      document.getElementById('autosave').textContent = 'Guardado local';
    }
  }

  function scheduleSync() {
    clearTimeout(syncTimer);
    syncTimer = setTimeout(syncWorkspace, 1000);
  }
  document.querySelectorAll('input,textarea,select').forEach(element => element.addEventListener('input', scheduleSync));
  document.getElementById('saveBtn')?.addEventListener('click', syncWorkspace);
  loadWorkspace();
})();