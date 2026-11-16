
// One integration point: Codex may replace /app with the existing application route.
const demoUrl = window.LUNARIS_DEMO_URL || '/app/';
document.querySelectorAll('.app-link').forEach(link => link.setAttribute('href', demoUrl));

const menu = document.querySelector('.menu-toggle');
const mobile = document.querySelector('.mobile-nav');
menu?.addEventListener('click', () => {
  const opened = menu.getAttribute('aria-expanded') === 'true';
  menu.setAttribute('aria-expanded', String(!opened));
  menu.setAttribute('aria-label', opened ? 'Open menu' : 'Close menu');
  mobile.hidden = opened;
});
mobile?.querySelectorAll('a').forEach(a => a.addEventListener('click', () => { mobile.hidden = true; menu?.setAttribute('aria-expanded', 'false'); }));

const chapters = [...document.querySelectorAll('.chapter')];
const camera = document.getElementById('scene-camera');
const stageLabel = document.getElementById('stage-label');
const stageCount = document.getElementById('stage-count');
const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
const smallScreen = window.matchMedia('(max-width: 700px)');
// Camera targets correspond to regions in the same continuous Dubai SVG.
// These are artistic viewport transforms, not geospatial coordinates.
const cameraTargets = {
  road: {desktop:[1.45, 10, -18], mobile:[1.15, -8, -9]},
  cafe: {desktop:[1.9, -23, 12], mobile:[1.35, -26, 6]},
  market: {desktop:[2.05, 18, 18], mobile:[1.4, 16, 12]},
  home: {desktop:[1.65, -17, -5], mobile:[1.2, -23, -8]},
  residence: {desktop:[1.55, 14, -5], mobile:[1.15, 10, -3]},
  park: {desktop:[1.75, -27, -18], mobile:[1.25, -30, -13]},
  overview: {desktop:[1.0, 0, 0], mobile:[1.0, 0, 0]}
};
let activeScene = null;
function updateStory() {
  if (reduceMotion.matches || !camera) return;
  const center = window.innerHeight * .5;
  let chosen = chapters[0];
  let bestDistance = Infinity;
  for (const chapter of chapters) {
    const bounds = chapter.getBoundingClientRect();
    const distance = Math.abs((bounds.top + bounds.bottom)/2 - center);
    if (distance < bestDistance) { bestDistance = distance; chosen = chapter; }
  }
  if (chosen !== activeScene) {
    activeScene = chosen;
    const target = cameraTargets[chosen.dataset.scene] || cameraTargets.overview;
    const [scale,x,y] = smallScreen.matches ? target.mobile : target.desktop;
    camera.style.transform = `translate3d(${x}%, ${y}%, 0) scale(${scale})`;
    if (stageLabel) stageLabel.textContent = chosen.dataset.label;
    if (stageCount) stageCount.textContent = chosen.dataset.number;
  }
}
let isTicking = false;
function scheduleUpdate() {
  if (isTicking) return;
  isTicking = true;
  window.requestAnimationFrame(() => {updateStory();isTicking = false;});
}
window.addEventListener('scroll', scheduleUpdate, {passive:true});
window.addEventListener('resize', () => { activeScene = null; scheduleUpdate(); }, {passive:true});
smallScreen.addEventListener?.('change', () => { activeScene=null; scheduleUpdate(); });
reduceMotion.addEventListener?.('change', scheduleUpdate);
updateStory();

const observer = new IntersectionObserver(entries => entries.forEach(entry => {
  if (entry.isIntersecting) { entry.target.classList.add('in-view'); observer.unobserve(entry.target); }
}), {threshold:.11});
document.querySelectorAll('.manifesto-inner,.section-heading,.tile,.journey-intro .container,.interlude-wrap,.global-copy,.final-inner').forEach(el => {el.classList.add('reveal');observer.observe(el)});
