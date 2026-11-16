const $ = (selector, root = document) => root.querySelector(selector);
const $$ = (selector, root = document) => [...root.querySelectorAll(selector)];
const STORAGE = { prefs: 'lunaris.preferences.v1', impact: 'lunaris.impact.v1', progress: 'lunaris.progress.v1' };

const TRAIL = [
  { key: 'preferences', label: 'Set your weather' },
  { key: 'forecast', label: 'Read a live forecast' },
  { key: 'heatshield', label: 'Compare better hours' },
  { key: 'choice', label: 'Run a sourced choice' },
  { key: 'action', label: 'Open an official action route' }
];

const state = {
  prefs: readJson(STORAGE.prefs) || { moods: ['rainy_cozy', 'cloudy_moody'], min: 19, max: 29 },
  forecast: null,
  activity: 'walk',
  route: 'home'
};

function readJson(key) {
  try { return JSON.parse(localStorage.getItem(key)); } catch { return null; }
}

function writeJson(key, value) {
  try { localStorage.setItem(key, JSON.stringify(value)); return true; } catch { return false; }
}

function markProgress(key) {
  const progress = readJson(STORAGE.progress) || {};
  if (!progress[key]) {
    progress[key] = new Date().toISOString();
    writeJson(STORAGE.progress, progress);
  }
  renderLumi();
}

function renderLumi() {
  const progress = readJson(STORAGE.progress) || {};
  const complete = TRAIL.filter(item => progress[item.key]).length;
  const messages = [
    'Start with the weather you actually enjoy. Your preferences stay in this browser.',
    'Nice. Now let’s read a live Dubai forecast—no invented conditions.',
    'The forecast is in. Compare the hours that fit you best.',
    'You found a better window. Next, put a real number behind one everyday choice.',
    'That estimate has a receipt. When you’re ready, open an official route to local action.',
    'Trail complete. No streak to protect—come back when the city or your plans change.'
  ];
  $('#lumi-message').textContent = messages[complete];
  $('#lumi-trail').innerHTML = TRAIL.map((item, index) => `<div class="trail-step ${progress[item.key] ? 'complete' : ''}"><span>${progress[item.key] ? '✓' : index + 1}</span><small>${item.label}</small></div>`).join('');
}

function showToast(message) {
  const toast = $('#toast');
  toast.textContent = message;
  toast.classList.add('show');
  window.clearTimeout(showToast.timer);
  showToast.timer = window.setTimeout(() => toast.classList.remove('show'), 3000);
}

function routeTo(route) {
  const valid = ['home', 'explore', 'heatshield', 'choices', 'action', 'impact'];
  if (!valid.includes(route)) route = 'home';
  state.route = route;
  $$('.screen').forEach(screen => screen.classList.toggle('active', screen.dataset.screen === route));
  $$('.dock-item').forEach(item => item.classList.toggle('active', item.dataset.route === route));
  history.replaceState(null, '', `#${route}`);
  window.scrollTo({ top: 0, behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth' });
  $('#main').focus({ preventScroll: true });
  if (route === 'heatshield' && state.forecast) markProgress('heatshield');
  if (route === 'impact') renderImpact();
}

function formatDubaiTime(date = new Date()) {
  return new Intl.DateTimeFormat('en', { timeZone: 'Asia/Dubai', hour: '2-digit', minute: '2-digit', hour12: false }).format(date);
}

function formatHour(iso) {
  return new Intl.DateTimeFormat('en', { timeZone: 'Asia/Dubai', hour: 'numeric', hour12: true }).format(parseDubaiTime(iso));
}

function formatDay(iso) {
  return new Intl.DateTimeFormat('en', { timeZone: 'Asia/Dubai', weekday: 'short' }).format(parseDubaiTime(iso));
}

function parseDubaiTime(iso) {
  return new Date(/[zZ]|[+-]\d\d:\d\d$/.test(iso) ? iso : `${iso}:00+04:00`);
}

function weatherLabel(code) {
  if (code === 0) return 'Clear sky';
  if ([1,2,3].includes(code)) return 'Cloud in the frame';
  if ([45,48].includes(code)) return 'Low visibility';
  if (code >= 51 && code <= 67) return 'Rain possible';
  if (code >= 80 && code <= 82) return 'Showers possible';
  if (code >= 95) return 'Storm conditions';
  return 'Forecast available';
}

async function loadWeather() {
  const url = 'https://api.open-meteo.com/v1/forecast?latitude=25.2048&longitude=55.2708&current=temperature_2m,apparent_temperature,is_day,weather_code&hourly=temperature_2m,apparent_temperature,relative_humidity_2m,precipitation_probability,weather_code,is_day&timezone=Asia%2FDubai&forecast_days=3';
  try {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), 9000);
    const response = await fetch(url, { signal: controller.signal });
    clearTimeout(timer);
    if (!response.ok) throw new Error(`Forecast source returned ${response.status}`);
    const data = await response.json();
    if (!data.current || !data.hourly || !Array.isArray(data.hourly.time)) throw new Error('Forecast response was incomplete');
    state.forecast = data;
    markProgress('forecast');
    renderWeather();
  } catch (error) {
    renderWeatherFailure();
  }
}

function renderWeather() {
  const { current } = state.forecast;
  $('#weather-temp').textContent = `${Math.round(current.temperature_2m)}°`;
  $('#weather-state').textContent = weatherLabel(current.weather_code);
  const within = current.temperature_2m >= state.prefs.min && current.temperature_2m <= state.prefs.max;
  const hazardous = current.apparent_temperature >= 40 || current.weather_code >= 95;
  $('#day-narrative').textContent = hazardous
    ? 'Conditions deserve care today. Compare a later hour and keep plans flexible.'
    : within
      ? 'The air is inside your chosen comfort range. A rare little alignment.'
      : 'Your better hours may arrive later. We found the closest forecast windows.';
  $('#weather-note').textContent = `Live model forecast retrieved ${formatDubaiTime()} Dubai time · Open-Meteo · not a street-level measurement.`;
  $('#heat-source').textContent = `Open-Meteo model forecast · retrieved ${formatDubaiTime()} · Dubai grid point`;
  renderWindows();
}

function renderWeatherFailure() {
  $('#weather-temp').textContent = '—°';
  $('#weather-state').textContent = 'Source unavailable';
  $('#day-narrative').textContent = 'The photograph stays. Live conditions do not. Try the source again soon.';
  $('#weather-note').textContent = 'The forecast source could not be verified, so LUNARIS is not displaying weather values or recommended windows.';
  $('#home-windows').innerHTML = '<div class="empty-line">Forecast unavailable. No conditions have been invented.</div>';
  $('#heat-windows').innerHTML = '<div class="empty-line dark">Open-Meteo is unavailable. HeatShield cannot rank windows without source data.</div>';
  $('#heat-source').textContent = 'Forecast unavailable · recommendations disabled';
}

function rankedWindows() {
  if (!state.forecast) return [];
  const h = state.forecast.hourly;
  const now = Date.now();
  return h.time.map((time, i) => ({
    time,
    temp: h.temperature_2m[i],
    apparent: h.apparent_temperature[i],
    humidity: h.relative_humidity_2m[i],
    rain: h.precipitation_probability[i],
    code: h.weather_code[i],
    isDay: h.is_day[i]
  })).filter(x => parseDubaiTime(x.time).getTime() > now + 30 * 60 * 1000)
    .map(x => {
      const center = (state.prefs.min + state.prefs.max) / 2;
      const comfortDistance = x.temp < state.prefs.min ? state.prefs.min - x.temp : x.temp > state.prefs.max ? x.temp - state.prefs.max : Math.abs(x.temp - center) * .2;
      const rainPenalty = x.rain > 50 ? 5 : x.rain * .025;
      const heatPenalty = x.apparent >= 40 ? 12 : x.apparent >= 35 ? 5 : 0;
      const activityPenalty = state.activity === 'run' && x.apparent >= 32 ? 4 : 0;
      return { ...x, score: comfortDistance + rainPenalty + heatPenalty + activityPenalty };
    }).sort((a, b) => a.score - b.score).slice(0, 3);
}

function cautionFor(apparent) {
  if (apparent >= 40) return 'Elevated';
  if (apparent >= 35) return 'Moderate';
  return 'Lower';
}

function renderWindows() {
  const windows = rankedWindows();
  $('#home-windows').innerHTML = windows.map((w, i) => `
    <div class="time-slot"><span class="time">${formatHour(w.time)}</span><div><strong>${i === 0 ? 'Closest fit' : 'Alternate window'}</strong><br><span>${formatDay(w.time)} · ${weatherLabel(w.code)}</span></div><strong class="temp">${Math.round(w.temp)}°</strong></div>
  `).join('');
  $('#heat-windows').innerHTML = windows.map((w, i) => `
    <article class="window-card"><div class="rank">0${i + 1}</div><div><h3>${formatDay(w.time)} · ${formatHour(w.time)}</h3><small>${weatherLabel(w.code)} · model forecast</small></div><div class="window-metric"><span>Air</span><strong>${Math.round(w.temp)}°C</strong></div><div class="window-metric"><span>Feels like</span><strong>${Math.round(w.apparent)}°C</strong></div><div class="window-metric"><span>Caution</span><strong class="${w.apparent >= 35 ? 'caution' : ''}">${cautionFor(w.apparent)}</strong></div></article>
  `).join('');
}

function addImpact(type, title, detail) {
  const records = readJson(STORAGE.impact) || [];
  records.unshift({ id: crypto.randomUUID ? crypto.randomUUID() : String(Date.now()), type, title, detail, at: new Date().toISOString() });
  writeJson(STORAGE.impact, records.slice(0, 30));
}

function renderImpact() {
  const records = readJson(STORAGE.impact) || [];
  const estimates = records.filter(r => r.type === 'estimated').length;
  const self = records.filter(r => r.type === 'official-route').length;
  $('#estimate-count').textContent = estimates;
  $('#self-count').textContent = self;
  if (!records.length) {
    $('#impact-list').innerHTML = '<div class="empty-ledger"><span>✦</span><h2>Your ledger is open.</h2><p>Run a sourced comparison to keep a private, browser-only record here.</p></div>';
    return;
  }
  $('#impact-list').innerHTML = records.map(r => `
    <article class="impact-record"><time>${new Intl.DateTimeFormat('en', { dateStyle: 'medium' }).format(new Date(r.at))}</time><div><h3>${escapeHtml(r.title)}</h3><span>${escapeHtml(r.detail)}</span></div><span class="record-tag">${escapeHtml(r.type)}</span></article>
  `).join('');
}

function escapeHtml(value) {
  return String(value).replace(/[&<>'"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;' }[c]));
}

function bindForms() {
  $('#preferences-form').addEventListener('submit', event => {
    event.preventDefault();
    const moods = $$('input[name="mood"]:checked').map(input => input.value);
    const min = Number($('#comfort-min').value);
    const max = Number($('#comfort-max').value);
    if (min >= max) { showToast('Choose a minimum below your maximum.'); return; }
    state.prefs = { moods: moods.length ? moods : ['cloudy_moody'], min, max };
    writeJson(STORAGE.prefs, state.prefs);
    markProgress('preferences');
    $('#onboarding').close();
    if (state.forecast) renderWeather();
    showToast('Your weather preferences are saved in this browser.');
  });

  $('#travel-form').addEventListener('submit', event => {
    event.preventDefault();
    const distance = Math.max(.1, Number($('#distance').value));
    const occupancy = Math.max(1, Number($('#occupancy').value));
    const results = [
      { name: 'Private car', value: distance * .16591 / occupancy },
      { name: 'Local bus', value: distance * .10151 },
      { name: 'Rail proxy', value: distance * .02121 },
      { name: 'Walk / cycle', value: 0 }
    ];
    const max = Math.max(...results.map(r => r.value), .01);
    $('#travel-results').innerHTML = results.map(r => `<div class="bar-row"><span>${r.name}</span><div class="bar-track"><div class="bar-fill" style="width:${Math.max(r.value / max * 100, r.value === 0 ? 0 : 3)}%"></div></div><strong>${r.value.toFixed(2)} kg CO₂e</strong></div>`).join('');
    addImpact('estimated', `${distance.toFixed(1)} km travel comparison`, 'UK Government 2026 factors · rail is a transparent London Underground proxy · no route inferred');
    markProgress('choice');
    showToast('Comparison added to your private impact ledger.');
  });

  $('#food-form').addEventListener('submit', event => {
    event.preventDefault();
    const factors = { beef: 99.48, poultry: 9.87, cheese: 23.88, rice: 4.45, tofu: 3.16, peas: .98 };
    const labels = { beef: 'Beef (beef herd)', poultry: 'Poultry', cheese: 'Cheese', rice: 'Rice', tofu: 'Tofu', peas: 'Peas' };
    const mass = Math.max(10, Number($('#food-mass').value)) / 1000;
    const a = $('#food-a').value, b = $('#food-b').value;
    const av = factors[a] * mass, bv = factors[b] * mass;
    $('#food-results').textContent = `${labels[a]}: ${av.toFixed(2)} kg CO₂e · ${labels[b]}: ${bv.toFixed(2)} kg CO₂e for ${Math.round(mass * 1000)} g.`;
    addImpact('estimated', `${labels[a]} / ${labels[b]} food comparison`, 'Our World in Data · Poore & Nemecek (2018) global lifecycle averages · not product-specific');
    markProgress('choice');
  });

  $('#energy-form').addEventListener('submit', event => {
    event.preventDefault();
    const kwh = Math.max(0, Number($('#monthly-kwh').value));
    const slabs = [[2000, .23], [2000, .28], [2000, .32], [Infinity, .38]];
    let remaining = kwh, base = 0;
    for (const [limit, rate] of slabs) {
      const units = Math.min(remaining, limit);
      base += units * rate;
      remaining -= units;
      if (remaining <= 0) break;
    }
    const fuel = kwh * .06;
    const vat = (base + fuel) * .05;
    const total = base + fuel + vat;
    $('#energy-results').textContent = `AED ${total.toFixed(2)} estimated electricity charge · base AED ${base.toFixed(2)} + fuel AED ${fuel.toFixed(2)} + VAT AED ${vat.toFixed(2)}. Other bill items excluded.`;
    addImpact('estimated', `${kwh.toFixed(0)} kWh DEWA estimate`, `AED ${total.toFixed(2)} · official November 2026 published rates · other bill items excluded`);
    markProgress('choice');
  });
}

function bindUi() {
  $$('[data-route]').forEach(button => button.addEventListener('click', () => routeTo(button.dataset.route)));
  $('#settings-button').addEventListener('click', () => openPreferences());
  $$('.activity').forEach(button => button.addEventListener('click', () => {
    $$('.activity').forEach(b => b.classList.remove('active'));
    button.classList.add('active');
    state.activity = button.dataset.activity;
    if (state.forecast) renderWindows();
  }));
  $$('.tool-tab').forEach(tab => tab.addEventListener('click', () => {
    $$('.tool-tab').forEach(t => t.classList.remove('active'));
    $$('.tool-panel').forEach(panel => panel.classList.remove('active'));
    tab.classList.add('active');
    $(`#${tab.dataset.tool}-tool`).classList.add('active');
  }));
  $$('.filter').forEach(filter => filter.addEventListener('click', () => {
    $$('.filter').forEach(f => f.classList.remove('active'));
    filter.classList.add('active');
    $$('[data-moods]').forEach(card => { card.hidden = filter.dataset.filter !== 'all' && card.dataset.moods !== filter.dataset.filter; });
  }));
  $$('[data-action-link]').forEach(link => link.addEventListener('click', () => {
    markProgress('action');
    addImpact('official-route', 'Opened an official volunteering route', 'External provider opened · no registration or outcome claimed by LUNARIS');
    showToast('Official route opened. Registration stays with the provider.');
  }));
}

function openPreferences() {
  $('#comfort-min').value = state.prefs.min;
  $('#comfort-max').value = state.prefs.max;
  $$('input[name="mood"]').forEach(input => { input.checked = state.prefs.moods.includes(input.value); });
  $('#onboarding').showModal();
}

function init() {
  bindUi();
  bindForms();
  renderLumi();
  $('#dubai-time').textContent = `${formatDubaiTime()} GST`;
  setInterval(() => { $('#dubai-time').textContent = `${formatDubaiTime()} GST`; }, 60000);
  routeTo(location.hash.slice(1) || 'home');
  renderImpact();
  if (!readJson(STORAGE.prefs)) setTimeout(openPreferences, 450);
  loadWeather();
}

init();
