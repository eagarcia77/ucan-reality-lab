// Legacy compatibility shim. The institutional header, footer, logos and theme
// are now managed by /institutional-shell.js on active pages.
(()=>{if(!document.querySelector('script[src*="institutional-shell.js"]')){const s=document.createElement('script');s.src='/institutional-shell.js?v=10000';document.head.appendChild(s);}})();