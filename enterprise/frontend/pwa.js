(()=>{
'use strict';
let deferredPrompt=null;
function addInstallUI(){
  if(document.getElementById('ucanInstallApp'))return;
  const host=document.querySelector('.ucan-shell-actions')||document.querySelector('header .row')||document.body;
  const button=document.createElement('button');
  button.id='ucanInstallApp';
  button.type='button';
  button.textContent='Instalar aplicación';
  button.hidden=true;
  button.addEventListener('click',async()=>{
    if(!deferredPrompt)return;
    deferredPrompt.prompt();
    await deferredPrompt.userChoice.catch(()=>null);
    deferredPrompt=null;
    button.hidden=true;
  });
  host.appendChild(button);
  const status=document.createElement('span');
  status.id='ucanConnectionStatus';
  status.setAttribute('role','status');
  status.style.cssText='font-weight:700;font-size:.9rem;padding:.35rem .55rem;border-radius:999px;background:#e4f0eb;color:#075e49';
  host.appendChild(status);
  const update=()=>{status.textContent=navigator.onLine?'En línea':'Modo sin conexión';status.title=navigator.onLine?'La conexión a Internet está disponible.':'El Studio local continúa disponible; IA y bibliotecas externas pueden no funcionar.'};
  addEventListener('online',update);addEventListener('offline',update);update();
  addEventListener('beforeinstallprompt',e=>{e.preventDefault();deferredPrompt=e;button.hidden=false;});
  addEventListener('appinstalled',()=>{button.hidden=true;deferredPrompt=null;});
}
async function register(){
  if(!('serviceWorker' in navigator))return;
  try{const reg=await navigator.serviceWorker.register('/service-worker.js',{scope:'/'});reg.update().catch(()=>{});}catch(e){console.warn('UCAN PWA:',e);}
}
document.readyState==='loading'?document.addEventListener('DOMContentLoaded',()=>{addInstallUI();register();}):(()=>{addInstallUI();register();})();
})();