(() => {
  const fileInput = document.getElementById('resourceFile');
  const urlInput = document.getElementById('resourceUrl');
  const typeInput = document.getElementById('resourceType');
  if (!fileInput || !urlInput || !typeInput) return;

  const get = id => document.getElementById(id);
  const API = location.hostname.endsWith('onrender.com')
    ? 'https://ucan-reality-lab.onrender.com/api'
    : '/api';
  const token = () => localStorage.getItem('ucan_access_token') || '';
  const params = new URLSearchParams(location.search);
  const course = params.get('course') || '';
  const level = params.get('level') || 'Universitario';
  const projectTitle = params.get('title') || 'Actividad educativa';
  let currentImage = '';
  let running = false;

  const panel = document.createElement('section');
  panel.id = 'imageAiPanel';
  panel.style.cssText = 'margin:1rem 0;padding:1rem;border:1px solid #9cb9ae;border-radius:14px;background:#f5fbf8';
  panel.innerHTML = `
    <div style="display:flex;justify-content:space-between;gap:1rem;align-items:center;flex-wrap:wrap">
      <div>
        <strong>Diseño automático desde imagen</strong>
        <div id="imageAiStatus" style="margin-top:.35rem;color:#52675f">Suba una imagen o pegue una URL HTTPS. La actividad se creará automáticamente.</div>
      </div>
      <button id="analyzeImageNow" type="button">Analizar nuevamente</button>
    </div>
    <div id="imageAiConcepts" style="margin-top:.75rem"></div>`;
  const preview = document.getElementById('resourcePreview');
  preview.parentNode.insertBefore(panel, preview.nextSibling);

  const status = get('imageAiStatus');
  const concepts = get('imageAiConcepts');
  const button = get('analyzeImageNow');

  function setStatus(message, kind = 'normal') {
    status.textContent = message;
    status.style.color = kind === 'error' ? '#a32323' : kind === 'success' ? '#08775d' : '#52675f';
  }

  function isImageUrl(value) {
    return /^https:\/\//i.test(value) && (typeInput.value === 'Imagen' || /\.(png|jpe?g|webp|gif|avif|svg)(\?|#|$)/i.test(value));
  }

  function readFile(file) {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = () => resolve(String(reader.result || ''));
      reader.onerror = () => reject(new Error('No fue posible leer la imagen.'));
      reader.readAsDataURL(file);
    });
  }

  async function compressImage(file) {
    const original = await readFile(file);
    if (file.size <= 3_000_000 || file.type === 'image/svg+xml' || file.type === 'image/gif') return original;
    return new Promise((resolve) => {
      const image = new Image();
      image.onload = () => {
        const max = 1800;
        const scale = Math.min(1, max / Math.max(image.width, image.height));
        const canvas = document.createElement('canvas');
        canvas.width = Math.max(1, Math.round(image.width * scale));
        canvas.height = Math.max(1, Math.round(image.height * scale));
        canvas.getContext('2d').drawImage(image, 0, 0, canvas.width, canvas.height);
        resolve(canvas.toDataURL('image/jpeg', 0.84));
      };
      image.onerror = () => resolve(original);
      image.src = original;
    });
  }

  function setValue(id, value) {
    const element = get(id);
    if (!element || value == null) return;
    element.value = Array.isArray(value) ? value.join('\n') : value;
    element.dispatchEvent(new Event('input', { bubbles: true }));
  }

  function replaceRubric(rows) {
    const rubric = get('rubric');
    if (!rubric || !Array.isArray(rows)) return;
    rubric.innerHTML = '';
    rows.forEach(row => {
      if (typeof window.criterionRow === 'function') return window.criterionRow(row);
      const item = document.createElement('div');
      item.className = 'rubric-row';
      item.innerHTML = '<input class="cname"><input class="cpoints" type="number" min="0" max="100"><input class="clevels"><button class="danger remove" type="button">Eliminar</button>';
      item.querySelector('.cname').value = row.name || '';
      item.querySelector('.cpoints').value = row.points || 0;
      item.querySelector('.clevels').value = row.levels || '';
      item.querySelector('.remove').onclick = () => { item.remove(); document.getElementById('rubricTotal')?.click(); };
      rubric.appendChild(item);
    });
  }

  function guidedDesign() {
    const goal = get('resourceDescription')?.value.trim() || projectTitle;
    const topic = goal.length > 120 ? goal.slice(0, 120) : goal;
    setValue('activityTitle', `Análisis visual aplicado: ${topic}`);
    setValue('bloom', level.toLowerCase().includes('doctor') || level.toLowerCase().includes('maestr') ? 'Evaluar' : 'Analizar');
    setValue('objectives', `1. Identificar con precisión los elementos principales observados en la imagen.\n2. Explicar las relaciones y funciones de los componentes identificados.\n3. Aplicar los conceptos de ${course || 'la materia'} mediante evidencia visual.\n4. Comunicar conclusiones claras y fundamentadas.`);
    setValue('instructions', `Observe cuidadosamente la imagen desde una perspectiva académica. Identifique sus componentes, organización y detalles relevantes. Relacione lo observado con los conceptos de ${course || 'este curso'}, documente evidencia visual y prepare una explicación fundamentada. Revise la rúbrica antes de entregar la actividad.`);
    setValue('question', `¿Cuáles son los elementos principales de la imagen, cómo se relacionan entre sí y qué evidencia visual sustenta su análisis?`);
    setValue('expected', 'La respuesta debe identificar elementos verificables, explicar relaciones o funciones, aplicar conceptos del curso, utilizar evidencia visual y presentar una conclusión organizada.');
    setValue('quiz1', 'Identifique tres elementos visibles y explique la importancia de cada uno.');
    setValue('quiz2', '¿Qué relación existe entre los componentes observados?');
    setValue('quiz3', '¿Cómo aplicaría este análisis a una situación auténtica del curso?');
    replaceRubric([
      { name:'Identificación y dominio del contenido', points:25, levels:'Excelente, competente, en desarrollo e insuficiente' },
      { name:'Análisis y evidencia visual', points:30, levels:'Excelente, competente, en desarrollo e insuficiente' },
      { name:'Aplicación y pensamiento crítico', points:25, levels:'Excelente, competente, en desarrollo e insuficiente' },
      { name:'Organización y comunicación', points:20, levels:'Excelente, competente, en desarrollo e insuficiente' }
    ]);
    if (typeof window.refresh === 'function') window.refresh();
    if (typeof window.quality === 'function') window.quality();
    if (typeof window.save === 'function') window.save();
    setStatus('Actividad inicial creada automáticamente. La IA está mejorando el contenido…', 'success');
  }

  function applyDesign(data) {
    setValue('activityTitle', data.activity_title);
    setValue('bloom', data.bloom_level);
    setValue('objectives', data.objectives);
    setValue('instructions', data.instructions);
    setValue('question', data.main_question);
    setValue('expected', data.expected_answer);
    (data.quiz || []).slice(0, 3).forEach((question, index) => setValue(`quiz${index + 1}`, question));
    setValue('modelAlt', data.model_accessibility_description);
    replaceRubric(data.rubric);
    if (data.image_summary) setValue('resourceDescription', data.image_summary);
    const tags = [...(data.detected_concepts || []), ...(data.model_search_terms || [])];
    concepts.innerHTML = tags.length
      ? `<strong>Conceptos y términos sugeridos:</strong> ${tags.map(x => `<span style="display:inline-block;margin:.2rem;padding:.25rem .55rem;border-radius:999px;background:#e5f4ee;color:#075e49">${String(x).replace(/[<>&"]/g, '')}</span>`).join('')}`
      : '';
    if (typeof window.refresh === 'function') window.refresh();
    if (typeof window.quality === 'function') window.quality();
    if (typeof window.save === 'function') window.save();
    setStatus(data.source === 'multimodal-ai'
      ? 'La IA analizó la imagen y completó la actividad. Revise el contenido antes de publicarlo.'
      : 'La actividad fue creada en modo guiado porque la IA visual no está configurada.', 'success');
  }

  async function analyze(imageValue = currentImage) {
    if (running) return;
    if (!imageValue) {
      const candidate = urlInput.value.trim();
      if (!isImageUrl(candidate)) return setStatus('Seleccione una imagen o escriba una URL HTTPS válida.', 'error');
      imageValue = candidate;
    }

    guidedDesign();
    if (!token()) return setStatus('La actividad inicial fue creada, pero la sesión expiró y la IA no pudo mejorarla. Inicie sesión nuevamente.', 'error');

    running = true;
    button.disabled = true;
    button.textContent = 'Analizando…';
    try {
      const response = await fetch(`${API}/ai/design-from-image`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token()}` },
        body: JSON.stringify({
          image_url: imageValue,
          project_title: projectTitle,
          course,
          academic_level: level,
          teacher_goal: get('resourceDescription')?.value || '',
          language: 'es-PR'
        })
      });
      const body = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(body.detail || `Error ${response.status} al analizar la imagen.`);
      applyDesign(body);
    } catch (error) {
      setStatus(`La actividad inicial fue creada. La mejora con IA no se completó: ${error.message}`, 'error');
    } finally {
      running = false;
      button.disabled = false;
      button.textContent = 'Analizar nuevamente';
    }
  }

  fileInput.addEventListener('change', async event => {
    const file = event.target.files?.[0];
    if (!file || !file.type.startsWith('image/')) return;
    typeInput.value = 'Imagen';
    setStatus('Preparando la imagen y creando la actividad…');
    try {
      currentImage = await compressImage(file);
      window.ucanImageData = currentImage;
      setTimeout(() => analyze(currentImage), 100);
    } catch (error) {
      setStatus(error.message || 'No fue posible preparar la imagen.', 'error');
    }
  });

  let urlTimer;
  urlInput.addEventListener('input', () => {
    clearTimeout(urlTimer);
    const value = urlInput.value.trim();
    if (!isImageUrl(value)) return;
    currentImage = value;
    typeInput.value = 'Imagen';
    const preview = get('resourcePreview');
    if (preview) preview.innerHTML = `<img src="${value.replace(/"/g, '&quot;')}" alt="Imagen utilizada para crear la actividad" style="max-width:100%;max-height:520px">`;
    urlTimer = setTimeout(() => analyze(value), 650);
  });

  button.addEventListener('click', () => analyze());
})();