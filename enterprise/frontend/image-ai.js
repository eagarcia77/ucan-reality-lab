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
  let currentImage = '';
  let running = false;

  const panel = document.createElement('section');
  panel.id = 'imageAiPanel';
  panel.style.cssText = 'margin:1rem 0;padding:1rem;border:1px solid #9cb9ae;border-radius:14px;background:#f5fbf8';
  panel.innerHTML = `
    <div style="display:flex;justify-content:space-between;gap:1rem;align-items:center;flex-wrap:wrap">
      <div>
        <strong>Diseño automático desde imagen</strong>
        <div id="imageAiStatus" style="margin-top:.35rem;color:#52675f">Suba una imagen o escriba su URL. El sistema diseñará la actividad automáticamente.</div>
      </div>
      <button id="analyzeImageNow" type="button">Analizar imagen y crear actividad</button>
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
      if (typeof window.criterionRow === 'function') {
        window.criterionRow(row);
        return;
      }
      const item = document.createElement('div');
      item.className = 'rubric-row';
      item.innerHTML = `<input class="cname"><input class="cpoints" type="number" min="0" max="100"><input class="clevels"><button class="secondary remove" type="button">Eliminar</button>`;
      item.querySelector('.cname').value = row.name || '';
      item.querySelector('.cpoints').value = row.points || 0;
      item.querySelector('.clevels').value = row.levels || '';
      item.querySelector('.remove').onclick = () => item.remove();
      rubric.appendChild(item);
    });
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

    if (data.image_summary) {
      setValue('resourceDescription', data.image_summary);
    }
    const tags = [...(data.detected_concepts || []), ...(data.model_search_terms || [])];
    concepts.innerHTML = tags.length
      ? `<strong>Conceptos y términos sugeridos:</strong> ${tags.map(x => `<span style="display:inline-block;margin:.2rem;padding:.25rem .55rem;border-radius:999px;background:#e5f4ee;color:#075e49">${String(x).replace(/[<>&"]/g, '')}</span>`).join('')}`
      : '';

    if (typeof window.refresh === 'function') window.refresh();
    if (typeof window.quality === 'function') window.quality();
    if (typeof window.save === 'function') window.save();
    setStatus(
      data.source === 'multimodal-ai'
        ? 'La IA analizó la imagen y creó la actividad completa. Revise el contenido antes de publicarlo.'
        : 'Se creó un diseño guiado. Para análisis visual detallado, configure OPENAI_API_KEY en el backend.',
      'success'
    );
    document.getElementById('activityTitle')?.scrollIntoView({ behavior: 'smooth', block: 'center' });
  }

  async function analyze(imageValue = currentImage) {
    if (running) return;
    if (!imageValue) {
      const candidate = urlInput.value.trim();
      if (!isImageUrl(candidate)) {
        setStatus('Seleccione una imagen o escriba una URL HTTPS válida.', 'error');
        return;
      }
      imageValue = candidate;
    }
    if (!token()) {
      setStatus('La sesión expiró. Regrese a Mis proyectos e inicie sesión nuevamente.', 'error');
      return;
    }

    running = true;
    button.disabled = true;
    button.textContent = 'Analizando imagen…';
    setStatus('Analizando la imagen y diseñando objetivos, instrucciones, preguntas y rúbrica…');
    try {
      const params = new URLSearchParams(location.search);
      const response = await fetch(`${API}/ai/design-from-image`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token()}`
        },
        body: JSON.stringify({
          image_url: imageValue,
          project_title: params.get('title') || get('activityTitle')?.value || 'Actividad educativa',
          course: '',
          academic_level: 'Universitario',
          teacher_goal: get('resourceDescription')?.value || '',
          language: 'es-PR'
        })
      });
      const body = await response.json();
      if (!response.ok) throw new Error(body.detail || 'No fue posible analizar la imagen.');
      applyDesign(body);
    } catch (error) {
      setStatus(error.message || 'No fue posible analizar la imagen.', 'error');
    } finally {
      running = false;
      button.disabled = false;
      button.textContent = 'Analizar imagen y crear actividad';
    }
  }

  fileInput.addEventListener('change', async event => {
    const file = event.target.files?.[0];
    if (!file || !file.type.startsWith('image/')) return;
    try {
      currentImage = await readFile(file);
      typeInput.value = 'Imagen';
      setStatus('Imagen cargada. Iniciando el diseño automático…');
      setTimeout(() => analyze(currentImage), 250);
    } catch (error) {
      setStatus(error.message, 'error');
    }
  });

  let urlTimer;
  urlInput.addEventListener('input', () => {
    clearTimeout(urlTimer);
    const value = urlInput.value.trim();
    if (!isImageUrl(value)) return;
    currentImage = value;
    urlTimer = setTimeout(() => {
      setStatus('URL de imagen detectada. Iniciando el diseño automático…');
      analyze(value);
    }, 900);
  });

  button.addEventListener('click', () => analyze());
})();
