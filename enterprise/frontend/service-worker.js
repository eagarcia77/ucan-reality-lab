const CACHE='ucan-reality-lab-v11.2.0';
const CORE=[
  '/',
  '/index.html',
  '/authoring-v8.html',
  '/standalone-dashboard.js',
  '/authoring-standalone.js',
  '/institutional-shell.js',
  '/logo-inter-1.js',
  '/logo-inter-2.js',
  '/logo-ucan-1.js',
  '/logo-ucan-2.js',
  '/manifest.webmanifest',
  '/ucan-app-icon.svg'
];
self.addEventListener('install',event=>{
  event.waitUntil(caches.open(CACHE).then(cache=>cache.addAll(CORE)).then(()=>self.skipWaiting()));
});
self.addEventListener('activate',event=>{
  event.waitUntil(caches.keys().then(keys=>Promise.all(keys.filter(k=>k!==CACHE).map(k=>caches.delete(k)))).then(()=>self.clients.claim()));
});
self.addEventListener('fetch',event=>{
  const request=event.request;
  if(request.method!=='GET')return;
  const url=new URL(request.url);
  if(url.origin===location.origin){
    if(request.mode==='navigate'){
      event.respondWith(fetch(request).then(response=>{
        const clone=response.clone();caches.open(CACHE).then(c=>c.put(request,clone));return response;
      }).catch(()=>caches.match(request).then(r=>r||caches.match('/index.html'))));
      return;
    }
    event.respondWith(caches.match(request).then(cached=>cached||fetch(request).then(response=>{
      if(response.ok){const clone=response.clone();caches.open(CACHE).then(c=>c.put(request,clone));}
      return response;
    })));
    return;
  }
  if(['cdn.jsdelivr.net','unpkg.com'].includes(url.hostname)){
    event.respondWith(caches.match(request).then(cached=>cached||fetch(request).then(response=>{
      const clone=response.clone();caches.open(CACHE).then(c=>c.put(request,clone));return response;
    })));
  }
});