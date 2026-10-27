'use strict';
/* Decorative interactions only. No network requests; data handling remains in app.js. */
(() => {
const motionBtn=document.getElementById('motionSwitch');
const motionLabel=document.getElementById('motionLabel');
const stage=document.getElementById('brandStage');
const top=document.getElementById('top');
const root=document.documentElement;
const osReduce=window.matchMedia('(prefers-reduced-motion: reduce)');
let userPaused=false;
function actualOff(){return userPaused||osReduce.matches;}
function updateMotion(){
 const reduced=osReduce.matches;
 const inactive=userPaused||reduced;
 document.body.classList.toggle('motion-off',inactive);
 motionBtn.disabled=reduced;
 motionBtn.setAttribute('aria-pressed',String(inactive));
 const fa=root.lang==='fa';
 const label=reduced?(fa?'کاهش حرکت توسط سیستم فعال است':'System reduced motion active'):
   userPaused?(fa?'فعال‌کردن حرکت':'Resume motion'):(fa?'توقف حرکت':'Pause motion');
 motionBtn.setAttribute('aria-label',label);
 motionBtn.setAttribute('title',label);
 motionLabel.textContent=label;
}
motionBtn.addEventListener('click',()=>{userPaused=!userPaused;updateMotion()});
osReduce.addEventListener?.('change',updateMotion);
updateMotion();
let pointerFrame=0;
top.addEventListener('pointermove', e=>{
 if(actualOff()||e.pointerType==='touch')return;
 if(pointerFrame)return;
 pointerFrame=requestAnimationFrame(()=>{
  const rect=top.getBoundingClientRect();
  top.style.setProperty('--pointer-x',((e.clientX-rect.left)/rect.width*100).toFixed(1)+'%');
  top.style.setProperty('--pointer-y',((e.clientY-rect.top)/rect.height*100).toFixed(1)+'%');
  pointerFrame=0;
 });
},{passive:true});
let tiltFrame=0;
stage.addEventListener('pointermove',e=>{
 if(actualOff()||e.pointerType==='touch')return;
 if(tiltFrame)return;
 tiltFrame=requestAnimationFrame(()=>{
 const r=stage.getBoundingClientRect();
 stage.style.setProperty('--tiltX',(((e.clientY-r.top)/r.height)-.5)*-5+'deg');
 stage.style.setProperty('--tiltY',(((e.clientX-r.left)/r.width)-.5)*5+'deg');
 tiltFrame=0;
 });
},{passive:true});
stage.addEventListener('pointerleave',()=>{stage.style.setProperty('--tiltX','0deg');stage.style.setProperty('--tiltY','0deg')});
let scrollFrame=0;
function scrollProgress(){if(scrollFrame)return;scrollFrame=requestAnimationFrame(()=>{
 const max=Math.max(1,root.scrollHeight-window.innerHeight);
 root.style.setProperty('--read-progress',(Math.max(0,Math.min(100,window.scrollY/max*100))).toFixed(2)+'%');scrollFrame=0;
})}
window.addEventListener('scroll',scrollProgress,{passive:true});scrollProgress();
if('IntersectionObserver' in window){
 root.classList.add('js-motion');
 const observer=new IntersectionObserver(entries=>{for(const ent of entries) if(ent.isIntersecting){ent.target.classList.add('is-revealed');observer.unobserve(ent.target)}},{threshold:.06,rootMargin:'0px 0px 40px 0px'});
 document.querySelectorAll('.reveal-section').forEach(el=>observer.observe(el));
}
const lang=document.getElementById('lang');
function updateLanguageMotion(){updateMotion();}
lang.addEventListener('click',()=>queueMicrotask(updateLanguageMotion));
updateLanguageMotion();
motionBtn.addEventListener('click',updateLanguageMotion);
})();
