'use strict';
/* No dependency; progressively enhanced <details> menu. Links work with JavaScript disabled. */
(() => {
 const menu=document.querySelector('.mobile-menu');
 if(!menu)return;
 menu.querySelectorAll('nav a').forEach(a=>a.addEventListener('click',()=>{menu.open=false;}));
 document.addEventListener('keydown',ev=>{
  if(ev.key==='Escape' && menu.open){menu.open=false;menu.querySelector('summary').focus();}
 });
 document.addEventListener('pointerdown',ev=>{
  if(menu.open&&!menu.contains(ev.target))menu.open=false;
 },{passive:true});
})();
