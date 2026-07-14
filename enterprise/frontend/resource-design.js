(() => {
  const get = id => document.getElementById(id);
  const description = get('resourceDescription');
  const resourceUrl = get('resourceUrl');
  const resourceType = get('resourceType');
  const resourceFile = get('resourceFile');
  const activityTitle = get('activityTitle');
  const resourceSection = get('resourceSection');
  if (!description || !resourceUrl || !resourceType || !resourceSection) return;

  let timer;
  let lastSignature = '';
  let autoRunning = false;

  const panel = document.createElement('div');
  panel.id = 'resourceDesignPanel';
  panel.style.cssText = 'margin-top:1rem;padding:1rem;border:1px solid #b8d4c8;border-radius:14px;background:#f7fcfa';
  panel.innerHTML = `
    <div style="display:flex;justify-content:space-between;gap:1rem;align-items:center;flex-wrap:wrap">
      <div>
        <strong>Diseño automático de la actividad</strong>
        <div id="resourceDesignStatus" style="margin-top:.35rem;color:#52675f">Escriba el propósito educativo, pegue una dirección o suba un archivo. El sistema diseñará la actividad automáticamente.</div>
      </div>
      <button id="designResourceNow" type="button">Diseñar actividad ahora</button>
    </div>`;
  resourceSection.appendChild(panel);

  const status = get('resourceDesignStatus');
  const button = get('designResourceNow');

  function setStatus(message, kind = 'normal') {
    status.textContent = message;
    status.style.color = kind === 'error' ? '#a32323' : kind === 'success' ? '#08775d' : '#52675f';
  }

  function sourceText() {
    const parts = [
      description.value.trim(),
      resourceUrl.value.trim(),
      resourceFile?.files?.[0]?.name || '',
      resourceType.value || ''
    ].filter(Boolean);
    return parts.join(' — ');
  }

  function signature() {
    return `${resourceType.value}|${resourceUrl.value.trim()}|${description.value.trim()}|${resourceFile?.files?.[0]?.name || ''}`;
  }

  function ensureDescription() {
    if (description.value.trim()) return;
    const fileName = resourceFile?.files?.[0]?.name;
    const url = resourceUrl.value.trim();
    if (fileName) description.value = `Diseñar una actividad universitaria utilizando el recurso ${fileName}.`;
    else if (url) description.value = `Diseñar una actividad universitaria utilizando el recurso disponible en ${url}.`;
    description.dispatchEvent(new Event('input', { bubbles: true }));
  }

  function fallbackDesign() {
    ensureDescription();
    const topic = description.value.trim() || sourceText() || 'el recurso educativo seleccionado';
    const type = resourceType.value || 'Recurso';
    const set = (id, value) => {
      const element = get(id);
      if (!element) return;
      element.value = value;
      element.dispatchEvent(new Event('input', { bubbles: true }));
    };
    set('activityTitle', `Actividad de análisis: ${topic.slice(0, 90)}`);
    set('bloom', 'Analizar');
    set('objectives', `1. Identificar los conceptos y componentes principales presentes en el ${type.toLowerCase()}.\n2. Explicar las relaciones entre la información observada y los contenidos del curso.\n3. Aplicar el conocimiento mediante una situación auténtica.\n4. Comunicar conclusiones con evidencia, claridad y vocabulario disciplinar.`);
    set('instructions', `Examine cuidadosamente el ${type.toLowerCase()} y su contenido. Identifique ideas, componentes, datos o relaciones relevantes. Conecte sus observaciones con los conceptos del curso, sustente su análisis con evidencia del recurso y prepare una respuesta organizada. Revise la rúbrica antes de entregar.`);
    set('question', `¿Cuáles son los elementos o ideas principales del recurso y cómo se relacionan con el propósito educativo descrito? Sustente su respuesta con evidencia.`);
    set('expected', 'La respuesta debe identificar información verificable del recurso, explicar relaciones, aplicar conceptos del curso, utilizar evidencia y presentar una conclusión bien organizada.');
    set('quiz1', 'Identifique tres elementos o ideas esenciales del recurso.');
    set('quiz2', 'Explique la relación entre dos de los elementos identificados.');
    set('quiz3', '¿Cómo aplicaría este aprendizaje en una situación real o profesional?');
    if (typeof window.refresh === 'function') window.refresh();
    if (typeof window.quality === 'function') window.quality();
    if (typeof window.save === 'function') window.save();
  }

  function design(force = false) {
    if (autoRunning) return;
    const current = signature();
    const meaningful = description.value.trim().length >= 8 || resourceUrl.value.trim().length >= 8 || resourceFile?.files?.length;
    if (!meaningful) {
      setStatus('Añada una descripción, una dirección o un archivo para diseñar la actividad.', 'error');
      return;
    }
    if (!force && current === lastSignature) return;
    lastSignature = current;
    autoRunning = true;
    button.disabled = true;
    button.textContent = 'Diseñando…';
    setStatus('Diseñando objetivos, instrucciones, preguntas y rúbrica…');
    try {
      if (typeof window.generate === 'function') {
        ensureDescription();
        window.generate('actividad');
      } else {
        fallbackDesign();
      }
      setStatus('Actividad diseñada automáticamente. Revise los campos y haga los ajustes necesarios.', 'success');
      activityTitle?.scrollIntoView({ behavior: 'smooth', block: 'center' });
    } catch (error) {
      fallbackDesign();
      setStatus(`Se creó una actividad guiada. ${error?.message || ''}`.trim(), 'success');
    } finally {
      autoRunning = false;
      button.disabled = false;
      button.textContent = 'Diseñar actividad ahora';
    }
  }

  function schedule() {
    clearTimeout(timer);
    timer = setTimeout(() => design(false), 900);
  }

  description.addEventListener('input', schedule);
  resourceUrl.addEventListener('input', () => {
    if (resourceType.value === 'Imagen') return; // image-ai.js handles visual analysis.
    schedule();
  });
  resourceType.addEventListener('change', schedule);
  resourceFile?.addEventListener('change', event => {
    const file = event.target.files?.[0];
    if (!file || file.type.startsWith('image/')) return; // image-ai.js handles images.
    ensureDescription();
    setTimeout(() => design(true), 120);
  });
  button.addEventListener('click', () => design(true));
})();