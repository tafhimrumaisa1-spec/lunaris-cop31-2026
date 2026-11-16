// Dubai tourism source-attributed editorial seed; no scraping of third-party map results.
const EXPLORE_VENUES = [{"name": "Spill the Bean", "type": "cafe", "area": "The Sustainable City", "evidence": "Visit Dubai describes reusable cup incentives, recycling and food-waste practices.", "source": "https://www.visitdubai.com/en/restaurants/spill-the-bean", "sourceLabel": "Visit Dubai venue profile", "note": "Practice described in official tourism editorial; current operations need confirmation.", "terms": ["cafe", "indoors", "coffee", "plant-based"]}, {"name": "Atlantis, The Palm", "type": "hotel", "area": "Palm Jumeirah", "evidence": "Listed in the Dubai Sustainable Tourism Stamp Gold tier (2025 cycle).", "source": "https://www.dubaidet.gov.ae/en/about-det/initiatives/dubai-sustainable-tourism/dubai-sustainable-tourism-stamp", "sourceLabel": "Dubai DET award list", "note": "The stamp is a hotel-level recognition, not a meal or per-stay carbon score.", "terms": ["hotel", "indoor", "palm", "gold"]}, {"name": "DoubleTree by Hilton Dubai – Business Bay", "type": "hotel", "area": "Business Bay", "evidence": "Listed in the Dubai Sustainable Tourism Stamp Gold tier (2025 cycle).", "source": "https://www.dubaidet.gov.ae/en/about-det/initiatives/dubai-sustainable-tourism/dubai-sustainable-tourism-stamp", "sourceLabel": "Dubai DET award list", "note": "No claim about specific facilities, operating hours or footprint.", "terms": ["hotel", "indoor", "business bay", "gold"]}, {"name": "25Hours Hotel Dubai One Central", "type": "hotel", "area": "One Central / Trade Centre", "evidence": "Listed in the Dubai Sustainable Tourism Stamp Silver tier (2025 cycle).", "source": "https://www.dubaidet.gov.ae/en/about-det/initiatives/dubai-sustainable-tourism/dubai-sustainable-tourism-stamp/dst-stamp-silver-tier", "sourceLabel": "Dubai DET Silver tier list", "note": "Check current recognition and facilities directly before visiting.", "terms": ["hotel", "indoor", "trade centre", "silver"]}, {"name": "Crowne Plaza Dubai Marina", "type": "hotel", "area": "Dubai Marina", "evidence": "Listed in the Dubai Sustainable Tourism Stamp Silver tier (2025 cycle).", "source": "https://www.dubaidet.gov.ae/en/about-det/initiatives/dubai-sustainable-tourism/dubai-sustainable-tourism-stamp/dst-stamp-silver-tier", "sourceLabel": "Dubai DET Silver tier list", "note": "Recognition does not establish lower emissions than other Dubai hotels.", "terms": ["hotel", "indoor", "marina", "silver"]}, {"name": "Address Dubai Mall", "type": "hotel", "area": "Downtown Dubai", "evidence": "Listed in the Dubai Sustainable Tourism Stamp Silver tier (2025 cycle).", "source": "https://www.dubaidet.gov.ae/en/about-det/initiatives/dubai-sustainable-tourism/dubai-sustainable-tourism-stamp/dst-stamp-silver-tier", "sourceLabel": "Dubai DET Silver tier list", "note": "This is a sourced hospitality listing, not an endorsement.", "terms": ["hotel", "indoor", "downtown", "silver"]}];
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
  aiWindows: null,
  aiStatus: null,
  aiRequestSeq: 0,
  route: 'home'
};

function readJson(key) {
  try { return JSON.parse(localStorage.getItem(key)); } catch { return null; }
}

function writeJson(key, value) {
  try { localStorage.setItem(key, JSON.stringify(value)); return true; } catch { return false; }
}

// Optional pseudonymous preference sync. The current experience works locally when the API is offline.
// This is NOT verified login or cross-device synchronization; no precise location is collected.
async function syncGuestPreferences(preferences) {
  const base=String(window.LUNARIS_API_BASE || '').replace(/\/$/, '');
  try {
    let token=sessionStorage.getItem('lunaris.atlas.guest_token');
    if (!token) {
      const issued=await fetch(`${base}/v1/session`,{method:'POST',headers:{'Content-Type':'application/json'},signal:AbortSignal.timeout(7000)});
      if (!issued.ok) return false;
      const body=await issued.json(); token=body.session_token;
      if (!token) return false;
      sessionStorage.setItem('lunaris.atlas.guest_token',token);
    }
    const res=await fetch(`${base}/v1/preferences`,{
      method:'PUT',headers:{'Content-Type':'application/json',Authorization:`Bearer ${token}`},
      body:JSON.stringify({city_id:'dubai',weather_moods:preferences.moods,
        comfort_min_c:preferences.min,comfort_max_c:preferences.max,
        activities:[],priorities:[],notification_consent:false}),
      signal:AbortSignal.timeout(7000)
    });
    return res.ok;
  } catch { return false; }
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

function renderDiscover() {
  const target = $('#discovery-results');
  if (!target) return;
  const kind = $('#discover-kind')?.value || 'all';
  const query = ($('#discover-search')?.value || '').trim().toLowerCase();
  const selected = EXPLORE_VENUES.filter(v =>
    (kind === 'all' || v.type === kind) &&
    (!query || [v.name, v.area, v.evidence, ...v.terms].join(' ').toLowerCase().includes(query))
  );
  if (!selected.length) {
    target.innerHTML = '<p class="discovery-empty">No matching reviewed venue in this small editorial catalogue. Try a different search or category.</p>';
    return;
  }
  target.innerHTML = selected.map(v => `<article class="discovery-card">
    <span class="discovery-kind">${v.type === 'cafe' ? 'CAFÉ / EDITORIAL PRACTICES' : 'HOTEL / OFFICIAL TOURISM STAMP'}</span>
    <h3>${escapeHtml(v.name)}</h3><p class="discovery-area">${escapeHtml(v.area)} · Dubai</p>
    <p>${escapeHtml(v.evidence)}</p><small>${escapeHtml(v.note)}</small>
    <div class="discovery-links"><a target="_blank" rel="noopener noreferrer" href="${v.source}">Read source ↗</a>
    <a target="_blank" rel="noopener noreferrer" href="https://www.openstreetmap.org/search?query=${encodeURIComponent(v.name+' '+v.area+' Dubai UAE')}">Find on map ↗</a></div>
  </article>`).join('');
}

function recommendedExplore(activity, setting, hour) {
  if (setting === 'indoor') return 'For indoor plans, Explore can show source-attributed venues; it does not certify indoor air temperature, accessibility or opening hours.';
  if (hour?.apparent >= 35) return 'Outdoor heat exposure deserves caution; consider shortening or changing plans. Explore has source-attributed venue options, but no verified indoor climate data.';
  if (activity === 'walk') return 'For a leisure walk, check shaded public paths and current access conditions; Explore venue evidence is not a mapped shade-route assessment.';
  return 'Check official alerts and the exact location before travelling. No site-level conditions have been verified.';
}

async function lookupBarcode(barcode) {
  if (!/^\d{8,14}$/.test(barcode)) throw new Error('Use an 8–14 digit barcode.');
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 8500);
  try {
    const response = await fetch(`https://world.openfoodfacts.org/api/v3/product/${encodeURIComponent(barcode)}?fields=product_name,brands,quantity,categories,ingredients_text,code`,
      { signal:controller.signal, headers:{ Accept:'application/json' }});
    if (!response.ok) throw Error('The product could not be retrieved.');
    const data = await response.json();
    if (!data.product || !(data.product.product_name || data.product.brands)) throw Error('Product identity not found.');
    return data.product;
  } finally { clearTimeout(timeout); }
}

function dewaElectricityComponent(units) {
  let remaining = Math.max(0, units), base = 0;
  for (const [limit, price] of [[2000,.23],[2000,.28],[2000,.32],[Infinity,.38]]) {
    const used = Math.min(remaining, limit); base += used*price; remaining-=used; if (remaining<=0) break;
  }
  return (base + Math.max(0,units)*.06)*1.05;
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
    refreshClimateAI();
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
  renderHeatDecision();
}

function renderWeatherFailure() {
  $('#weather-temp').textContent = '—°';
  $('#weather-state').textContent = 'Source unavailable';
  $('#day-narrative').textContent = 'The photograph stays. Live conditions do not. Try the source again soon.';
  $('#weather-note').textContent = 'The forecast source could not be verified, so LUNARIS is not displaying weather values or recommended windows.';
  $('#home-windows').innerHTML = '<div class="empty-line">Forecast unavailable. No conditions have been invented.</div>';
  $('#heat-windows').innerHTML = '<div class="empty-line dark">Open-Meteo is unavailable. HeatShield cannot rank windows without source data.</div>';
  $('#heat-source').textContent = 'Forecast unavailable · recommendations disabled';
  state.aiWindows = null;
  const plan = $('#heat-plan-summary');
  if (plan) plan.textContent = 'Live forecast unavailable: no timing or activity advice can be generated.';
}

function rankedWindows() {
  if (!state.forecast) return [];
  const h = state.forecast.hourly;
  const now = Date.now();
  const duration = Number($('#heat-duration')?.value || 30);
  const setting = $('#heat-exposure')?.value || 'exposed';
  const daypart = $('#heat-daypart')?.value || 'any';
  return h.time.map((time, i) => ({
    time,
    temp: h.temperature_2m[i],
    apparent: h.apparent_temperature[i],
    humidity: h.relative_humidity_2m[i],
    rain: h.precipitation_probability[i],
    code: h.weather_code[i],
    isDay: h.is_day[i]
  })).filter(x => parseDubaiTime(x.time).getTime() > now + 30 * 60 * 1000)
    .filter(x => { const hr = Number(x.time.slice(11,13)); return daypart === 'any' || (daypart === 'morning' && hr >= 5 && hr < 12) || (daypart === 'afternoon' && hr >= 12 && hr < 18) || (daypart === 'evening' && hr >= 18 && hr <= 23); })
    .map(x => {
      const plan = heatPlanFor(x, duration, setting, state.activity);
      if (!plan || !plan.complete) return null;
      const center = (state.prefs.min + state.prefs.max) / 2;
      const comfortDistance = x.temp < state.prefs.min ? state.prefs.min - x.temp : x.temp > state.prefs.max ? x.temp - state.prefs.max : Math.abs(x.temp - center) * .2;
      const rainPenalty = x.rain > 50 ? 5 : x.rain * .025;
      const heatPenalty = x.apparent >= 40 ? 12 : x.apparent >= 35 ? 5 : 0;
      const vigorous = ['run','cycle'].includes(state.activity);
      const activityPenalty = vigorous && x.apparent >= 32 ? 5 : 0;
      const sunPenalty = exposure === 'exposed' && x.isDay && x.apparent >= 30 ? 4 : 0;
      const longExposurePenalty = duration >= 60 && exposure !== 'indoor' && x.apparent >= 32 ? 5 : 0;
      return { ...x, score: comfortDistance + rainPenalty + heatPenalty + activityPenalty + sunPenalty + longExposurePenalty + (plan.apparent >= 40 ? 15 : plan.apparent >= 35 ? 8 : 0) + (plan.rain >= 50 ? 5 : 0) + Math.max(0,plan.apparent-x.apparent)*0.5 };
    }).filter(Boolean).sort((a, b) => a.score - b.score).slice(0, 3);
}

// Decision support only: this is an activity planner, not a clinical heat-stress model.
// We use forecast gridpoint apparent temperature, rainfall, daylight, and a selected
// duration; street shade and personal acclimatization cannot be inferred here.
function heatPlanFor(hour, duration, setting, activity) {
  const h = state.forecast?.hourly;
  if (!h) return null;
  const idx = h.time.indexOf(hour.time);
  if (idx < 0) return null;
  const numberOfHours = Math.max(1, Math.ceil(duration / 60));
  if (idx + numberOfHours > h.time.length) return null;
  const slice = Array.from({ length: numberOfHours }, (_, k) => idx + k);
  const apparent = Math.max(...slice.map(i => Number(h.apparent_temperature[i])).filter(Number.isFinite));
  const rain = Math.max(...slice.map(i => Number(h.precipitation_probability[i])).filter(Number.isFinite));
  if (!Number.isFinite(apparent) || !Number.isFinite(rain)) return null;
  const daylight = slice.some(i => Number(h.is_day[i]) === 1);
  const vigorous = activity === 'run' || activity === 'cycle';
  const notes = [];
  if (setting === 'indoor') notes.push('Indoor cooling conditions cannot be estimated from city weather. Verify the venue.');
  else {
    if (daylight && setting === 'exposed') notes.push('Daylight and unshaded surroundings may increase radiant heat exposure; seek shade.');
    if (apparent >= 40) notes.push('Very high apparent temperature; consider rescheduling outdoor exertion or moving indoors.');
    else if (apparent >= 35) notes.push('Elevated apparent temperature; shorten exposure and consider a lower-intensity alternative.');
    else if (apparent >= 30 && vigorous) notes.push('For sustained exercise, consider an easier intensity or cooler hour.');
    if (rain >= 55) notes.push('Rain is possible; review local alerts and conditions before departure.');
  }
  if (duration >= 60 && setting !== 'indoor') notes.push('Longer exposure adds uncertainty; plan breaks and access to drinking water.');
  if (!notes.length) notes.push('Forecast conditions are closer to your selected preferences; local conditions can still differ.');
  return {apparent, rain, notes, daylight, complete: true};
}

function renderHeatDecision() {
  const target = $('#heat-plan-summary');
  if (!target) return;
  if (!state.forecast) { target.textContent = 'Awaiting a live forecast. No timing decision has been calculated.'; return; }
  const duration = Number($('#heat-duration')?.value || 30);
  const setting = $('#heat-exposure')?.value || 'exposed';
  const activityLabel = {walk:'walk',run:'run',cycle:'cycle ride',outdoor:'outdoor visit'}[state.activity] || 'outdoor activity';
  if (setting === 'indoor') {
    target.textContent = `For a ${duration}-minute indoor plan, LUNARIS cannot assess conditions inside a specific business. Choose a venue with confirmed indoor facilities and opening hours. Outdoor travel still depends on the forecast.`;
    return;
  }
  // Use the same forecast for planning, including when the optional backend ML is absent.
  // Planned recommendations remain heuristic; no model-accuracy claim is attached.
  const hours = rankedWindows();
  if (!hours.length) {target.textContent='No eligible upcoming forecast hours. Try again later.';return;}
  const viable = hours.map(w=>({w,p:heatPlanFor(w,duration,setting,state.activity)})).filter(x=>x.p);
  if (!viable.length) {target.textContent='The required forecast data is incomplete.';return;}
  const {w,p}=viable[0];
  target.textContent = `For a ${duration}-minute ${activityLabel}, ${formatDay(w.time)} at ${formatHour(w.time)} is one of the closest forecast matches—not a safety clearance. Forecast peak apparent temperature across the planned hourly segment: ${Math.round(p.apparent)}°C; maximum listed rain chance: ${Math.round(p.rain)}%. ${p.notes.join(' ')} ${recommendedExplore(state.activity,setting,w)} Open-Meteo city-grid model; no street-level or medical risk assessment.`;
}

function cautionFor(apparent) {
  if (apparent >= 40) return 'Elevated';
  if (apparent >= 35) return 'Moderate';
  return 'Lower';
}

function renderWindows() {
  // A functioning backend can supply AI-evaluated predictions. Otherwise we retain
  // the existing explicitly heuristic Open-Meteo experience without claiming AI.
  if (state.aiWindows?.length) {
    const windows = state.aiWindows;
    const method = state.aiStatus === 'validation_gate_passed'
      ? 'Experimental ML correction on eligible forecast hours; planner uses the complete provider forecast interval'
      : 'Open-Meteo provider forecast; transparent preference ranking (not trained AI)';
    $('#heat-source').textContent = method;
    $('#home-windows').innerHTML = windows.slice(0, 3).map((w, i) => `
      <div class="time-slot"><span class="time">${formatHour(w.time)}</span><div><strong>${i === 0 ? 'Closest fit' : 'Alternate window'}</strong><br><span>${formatDay(w.time)} · ${escapeHtml(w.reason)}</span></div><strong class="temp">${Math.round(w.apparent_temperature_c)}°</strong></div>
    `).join('');
    $('#heat-windows').innerHTML = windows.map((w, i) => `
      <article class="window-card"><div class="rank">0${i + 1}</div><div><h3>${formatDay(w.time)} · ${formatHour(w.time)}</h3><small>${escapeHtml(w.reason)} · personal preference ranking</small></div><div class="window-metric"><span>Feels like</span><strong>${Math.round(w.apparent_temperature_c)}°C</strong></div><div class="window-metric"><span>Match</span><strong>${Math.round(w.preference_match_score)}/100</strong></div><div class="window-metric"><span>Caution</span><strong class="${w.cautions.length ? 'caution' : ''}">${w.cautions.length ? 'Review' : 'No flagged threshold'}</strong></div></article>
    `).join('');
    renderHeatDecision();
    return;
  }
  const windows = rankedWindows();
  $('#home-windows').innerHTML = windows.map((w, i) => `
    <div class="time-slot"><span class="time">${formatHour(w.time)}</span><div><strong>${i === 0 ? 'Closest fit' : 'Alternate window'}</strong><br><span>${formatDay(w.time)} · ${weatherLabel(w.code)}</span></div><strong class="temp">${Math.round(w.temp)}°</strong></div>
  `).join('');
  $('#heat-windows').innerHTML = windows.map((w, i) => `
    <article class="window-card"><div class="rank">0${i + 1}</div><div><h3>${formatDay(w.time)} · ${formatHour(w.time)}</h3><small>${weatherLabel(w.code)} · model forecast</small></div><div class="window-metric"><span>Air</span><strong>${Math.round(w.temp)}°C</strong></div><div class="window-metric"><span>Feels like</span><strong>${Math.round(w.apparent)}°C</strong></div><div class="window-metric"><span>Caution</span><strong class="${w.apparent >= 35 ? 'caution' : ''}">${cautionFor(w.apparent)}</strong></div></article>
  `).join('');
  renderHeatDecision();
}

// Optional backend integration. Set window.LUNARIS_API_BASE to the FastAPI origin
// when the backend is hosted separately; empty means same-origin. No fabricated
// demonstration predictions and no fake scores when the model is unavailable.
async function refreshClimateAI() {
  if (!state.forecast) return;
  const seq = ++state.aiRequestSeq;
  state.aiWindows = null;
  const base = String(window.LUNARIS_API_BASE || '').replace(/\/$/, '');
  const activityMap = { walk: 'walking', run: 'running', cycle: 'walking', outdoor: 'outdoor_rest' };
  try {
    const response = await fetch(`${base}/v1/heatshield/ai-windows`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        days: 3,
        limit: 6,
        preferences: {
          min_comfort_c: Number(state.prefs.min),
          max_comfort_c: Number(state.prefs.max),
          prefers_clouds: state.prefs.moods.includes('cloudy_moody'),
          prefers_rain: state.prefs.moods.includes('rainy_cozy'),
          prefer_evenings: state.prefs.moods.includes('after_dark'),
          activity: activityMap[state.activity] || 'walking'
        }
      })
    });
    if (!response.ok) throw new Error('Climate engine unavailable');
    const data = await response.json();
    if (seq !== state.aiRequestSeq) return;
    if (data.city !== 'Dubai' || !Array.isArray(data.windows)) throw new Error('Unexpected engine response');
    state.aiWindows = data.windows.filter(w => Number.isFinite(w.apparent_temperature_c) && Number.isFinite(w.preference_match_score) && Array.isArray(w.cautions));
    state.aiStatus = data.ml_status;
    renderWindows();
    const status = $('#ai-evaluation');
    if (status) status.textContent = data.ml_status === 'validation_gate_passed'
      ? 'Experimental ML correction passed the validation gate for eligible forecast hours. See model evaluation for test results.'
      : 'Using Open-Meteo forecast. No validated ML correction is active. Personal preference ranking is rule-based.';
  } catch {
    if (seq !== state.aiRequestSeq) return;
    state.aiStatus = 'api_unavailable';
    state.aiWindows = null;
    renderWindows();
    const status = $('#ai-evaluation');
    if (status) status.textContent = 'AI backend is not connected. Existing Open-Meteo weather and rule-based HeatShield remain available.';
  }
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

async function eraseGuestAndLocalData() {
  if (!window.confirm('Erase your browser preferences and LUNARIS contribution history? Any current guest session will also be deleted if the API can be reached.')) return;
  const message=$('#delete-status');
  if (message) message.textContent='Erasing...';
  const base=String(window.LUNARIS_API_BASE || '').replace(/\/$/, '');
  let remote='No guest session was active.';
  try {
    const token=sessionStorage.getItem('lunaris.atlas.guest_token');
    if (token) {
      const res=await fetch(`${base}/v1/me`,{method:'DELETE',headers:{Authorization:`Bearer ${token}`},signal:AbortSignal.timeout(7000)});
      remote=res.status===204?'Temporary guest account erased on server.':'Server erasure could not be confirmed; retry while online.';
    }
  } catch { remote='Server erasure could not be confirmed; retry while online.'; }
  // Preserve token if server deletion was not confirmed, allowing a later retry.
  for (const key of [STORAGE.prefs,STORAGE.impact,STORAGE.progress,'lunaris.atlas.local-interest.v1']) {
    try { localStorage.removeItem(key); } catch { /* storage disabled */ }
  }
  if (remote.includes('erased') || remote==='No guest session was active.') {
    try { sessionStorage.removeItem('lunaris.atlas.guest_token'); } catch { /* storage disabled */ }
  }
  state.prefs={moods:['rainy_cozy','cloudy_moody'],min:19,max:29};
  renderImpact(); renderLumi();
  if (message) message.textContent='Local browser records erased. '+remote;
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
    if (state.forecast) { renderWeather(); refreshClimateAI(); }
    showToast('Preferences saved on this device.');
    syncGuestPreferences(state.prefs).then(saved=>{if(saved)showToast('Preferences also saved to this temporary guest session.');});
  });

  $('#heat-duration')?.addEventListener('change',()=>{if(state.forecast)renderWindows();});
  $('#heat-daypart')?.addEventListener('change',()=>{if(state.forecast)renderWindows();});
  $('#heat-exposure')?.addEventListener('change',()=>{if(state.forecast)renderWindows();});
  $('#heat-explore')?.addEventListener('click',()=>{ $('#discover-kind').value='all'; $('#discover-search').value=''; renderDiscover(); routeTo('explore'); });
  $('#vehicle-fuel')?.addEventListener('change',()=>{
    const isEV=$('#vehicle-fuel').value==='ev';
    $('#vehicle-unit').textContent=isEV?'kWh/100 km':'L/100 km';
    $('#vehicle-alt-unit').textContent=isEV?'kWh/100 km':'L/100 km';
    $('#ev-grid-row').hidden=!isEV;
    $('#vehicle-efficiency').value=isEV?'16':'7';
  });
  $('#vehicle-form')?.addEventListener('submit',event=>{
    event.preventDefault();
    const fuel=$('#vehicle-fuel').value;
    const efficiency=Number($('#vehicle-efficiency').value), distance=Number($('#vehicle-distance').value), people=Number($('#vehicle-passengers').value);
    const altText=$('#vehicle-alt-efficiency').value.trim(), gridText=$('#vehicle-grid-factor').value.trim();
    const alternate=altText ? Number(altText):null, grid=gridText ? Number(gridText):null;
    const label=($('#vehicle-name').value.trim()||'This vehicle');
    const out=$('#vehicle-result');
    if (![efficiency,distance,people].every(Number.isFinite)||efficiency<=0||distance<=0||people<1||(alternate!==null&&(!Number.isFinite(alternate)||alternate<=0))||(grid!==null&&(!Number.isFinite(grid)||grid<0))) {out.textContent='Check trip length, efficiency and passengers.';return;}
    const units=efficiency*distance/100, compare=alternate===null?null:alternate*distance/100;
    if(fuel==='ev'){
      const factor=grid===null?'Local electricity factor not provided':`USER-SUPPLIED electricity factor ${grid} kg CO₂e/kWh`;
      const footprint=grid===null?'Emissions not calculated':`${(units*grid).toFixed(2)} kg CO₂e (${(units*grid/people).toFixed(2)} kg/passenger), excluding charging losses`;
      const other=compare===null?'':` Alternate EV efficiency: ${compare.toFixed(2)} kWh for the same trip${grid===null?'':` and ${(compare*grid).toFixed(2)} kg CO₂e using the same user-supplied factor`}.`;
      out.textContent=`${label}: ${units.toFixed(2)} kWh (${(units/people).toFixed(2)} kWh/passenger). ${factor}. ${footprint}.${other} Not a factory-certified model comparison or full lifecycle figure.`;
    } else {
      const factor=fuel==='diesel'?2.68:2.31;
      out.textContent=`${label}: ${units.toFixed(2)} L and approximately ${(units*factor).toFixed(2)} kg direct combustion CO₂ (${(units*factor/people).toFixed(2)} kg/passenger).${compare===null?'':` Alternative efficiency: ${compare.toFixed(2)} L and ${(compare*factor).toFixed(2)} kg direct CO₂ for the same trip.`} Based on user-provided efficiency; real-world driving and upstream/lifecycle emissions excluded.`;
    }
  });
  $('#product-lookup')?.addEventListener('submit',async event=>{
    event.preventDefault();
    const barcode=$('#product-barcode').value.trim();
    const out=$('#product-result');
    if(!/^\d{8,14}$/.test(barcode)){out.textContent='Enter a valid 8–14-digit barcode.';return;}
    out.textContent='Looking up the product in Open Food Facts…';
    try{
      const controller=new AbortController(); const timer=setTimeout(()=>controller.abort(),8500);
      const response=await fetch(`https://world.openfoodfacts.org/api/v3/product/${encodeURIComponent(barcode)}?fields=product_name,brands,quantity,categories,code`,{signal:controller.signal,headers:{Accept:'application/json'}});
      clearTimeout(timer);
      if(!response.ok)throw Error('Product lookup is unavailable');
      const data=await response.json();
      const product=data.product;
      if(!product || !(product.product_name||product.brands)) {out.textContent='No product identity was found for this barcode. No emissions can be inferred.';return;}
      out.textContent=`Open Food Facts: ${product.brands||'Brand not stated'} — ${product.product_name||'Unnamed product'} (${product.quantity||'size unknown'}). This identifies a product only. No verified brand-specific carbon footprint was returned; consult a published product LCA before comparing.`;
    }catch {out.textContent='Product lookup is unavailable. You can still compare source-published footprints manually below.';}
  });
  $('#discover-kind')?.addEventListener('change', renderDiscover);
  $('#discover-search')?.addEventListener('input', renderDiscover);
  $('#barcode-pair-form')?.addEventListener('submit',async event=>{
    event.preventDefault();
    const a = $('#barcode-a').value.trim(), b = $('#barcode-b').value.trim();
    const out = $('#barcode-pair-results');
    if (!/^\d{8,14}$/.test(a) || !/^\d{8,14}$/.test(b) || a === b) {out.textContent='Enter two different valid 8–14-digit barcodes.';return;}
    out.textContent = 'Checking the two product identities…';
    const results=await Promise.allSettled([lookupBarcode(a),lookupBarcode(b)]);
    out.innerHTML=results.map((r,i)=>{
      if(r.status!=='fulfilled') return `<article class="pair-entry"><h4>Product ${i===0?'A':'B'}</h4><p>Identity unavailable. Try another barcode when online.</p></article>`;
      const p=r.value;
      return `<article class="pair-entry"><span>PRODUCT ${i===0?'A':'B'}</span><h4>${escapeHtml(p.brands||'Brand unknown')} — ${escapeHtml(p.product_name||'Unspecified item')}</h4><p>${escapeHtml(p.quantity||'Size unknown')} · ${escapeHtml((p.ingredients_text||'Ingredient data not available').slice(0,200))}</p><a href="https://world.openfoodfacts.org/product/${encodeURIComponent(i===0?a:b)}" target="_blank" rel="noopener noreferrer">Open product record ↗</a></article>`;
    }).join('')+'<p class="comparison-warning">Identity and ingredients are not product-level CO₂e footprints. Do not infer a greener brand without comparable lifecycle assessments.</p>';
  });
  $('#appliance-kind')?.addEventListener('change',()=>{
    const examples={aircon:[1200,6,4],lighting:[12,6,4],fan:[60,10,7],computer:[100,8,6],custom:[100,6,4]};
    const [watts,oldHours,newHours]=examples[$('#appliance-kind').value];
    $('#appliance-watts').value=watts; $('#appliance-hours').value=oldHours; $('#appliance-new-hours').value=newHours;
  });
  $('#appliance-form')?.addEventListener('submit',event=>{
    event.preventDefault();
    const watts=Number($('#appliance-watts').value), count=Number($('#appliance-count').value);
    const before=Number($('#appliance-hours').value),after=Number($('#appliance-new-hours').value), monthly=Number($('#monthly-kwh').value);
    const out=$('#appliance-results');
    if(![watts,count,before,after,monthly].every(Number.isFinite)||watts<=0||count<1||before<0||after<0||before>24||after>24||monthly<0) {out.textContent='Review appliance values and usage hours.';return;}
    const use=watts*count*before*30/1000, updated=watts*count*after*30/1000;
    const delta=use-updated;
    if (delta>0 && delta>monthly) {out.textContent='This appliance scenario exceeds your entered household total. Check wattage, runtime or the monthly kWh baseline.';return;}
    const newMonthly=Math.max(0,monthly-delta),savings=dewaElectricityComponent(monthly)-dewaElectricityComponent(newMonthly);
    out.textContent=`Illustrative appliance usage: ${use.toFixed(1)} kWh/month before → ${updated.toFixed(1)} kWh/month after. ${delta>=0?`Modeled reduction ${delta.toFixed(1)} kWh/month`:`Modeled increase ${Math.abs(delta).toFixed(1)} kWh/month`}. At your entered household baseline ${monthly.toFixed(0)} kWh/month, the electricity-component bill change is ${savings>=0?'savings':'additional cost'} of approximately AED ${Math.abs(savings).toFixed(2)}/month. Rated wattage is not actual measured average draw; HVAC cycling, efficiency and actual days vary. No guaranteed savings.`;
  });
  $('#product-compare')?.addEventListener('submit',event=>{
    event.preventDefault();
    const nameA=$('#brand-a').value.trim(),nameB=$('#brand-b').value.trim();
    const a=Number($('#footprint-a').value),b=Number($('#footprint-b').value);
    const u1=$('#source-a').value.trim(),u2=$('#source-b').value.trim();
    const out=$('#product-comparison');
    if(!nameA||!nameB||![a,b].every(v=>Number.isFinite(v)&&v>0)){out.textContent='Enter exact product names and positive published footprints.';return;}
    if(![u1,u2].every(v=>{try{return new URL(v).protocol==='https:'}catch{return false}})){out.textContent='Provide two HTTPS source links before comparing.';return;}
    const boundary=$('#footprint-boundary').selectedOptions[0].textContent;
    const lower=a<b?nameA:nameB, diff=100*Math.abs(a-b)/Math.max(a,b);
    out.textContent=`User-entered reported values: ${nameA} ${a.toFixed(3)} versus ${nameB} ${b.toFixed(3)} kg CO₂e/kg (${boundary}). ${a===b?'Equal entered values.':`${lower} has a ${diff.toFixed(1)}% smaller entered value than the higher result.`} NOT a LUNARIS-verified ranking: the sources, product markets, dates and methods have not been checked for comparability. Source A: ${u1} | Source B: ${u2}`;
  });
  $('#energy-scenario-form')?.addEventListener('submit',event=>{
    event.preventDefault();
    const initial=Number($('#monthly-kwh').value),rate=Number($('#energy-reduction').value)/100;
    const slab=units=>{let remaining=units,base=0;for(const [limit,price] of [[2000,.23],[2000,.28],[2000,.32],[Infinity,.38]]){const n=Math.min(remaining,limit);base+=n*price;remaining-=n;if(remaining<=0)break;}return (base+units*.06)*1.05;};
    if(!Number.isFinite(initial)||initial<0||!Number.isFinite(rate)||rate<=0||rate>.6)return;
    const future=initial*(1-rate),savings=slab(initial)-slab(future);
    $('#energy-savings').textContent=`Scenario: ${initial.toFixed(0)} → ${future.toFixed(0)} kWh/month (−${(rate*100).toFixed(0)}%). Estimated DEWA electricity-component savings: AED ${savings.toFixed(2)} per month or AED ${(savings*12).toFixed(2)} over 12 equal months. Based on November 2026 published tariffs; not a guaranteed bill saving, future rates or an appliance-level prediction.`;
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
    if (state.forecast) { renderWindows(); refreshClimateAI(); }
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


// Lumi local guide v1: intentionally bounded knowledge and live state, NOT a generative LLM.
// Text is rendered with textContent to avoid turning user questions into HTML.
function lumiRespond(rawQuestion) {
  const q = String(rawQuestion || '').trim().toLowerCase();
  const observations = state.forecast;
  const reply = { title: 'Lumi · Evidence-aware guide', text: '', label: '', href: '' };
  if (!q) return null;
  if (/weather|temperature|forecast|humid|rain|hot today|dubai now/.test(q)) {
    const t = observations?.current?.temperature_2m;
    const apparent = observations?.current?.apparent_temperature;
    if (Number.isFinite(t)) {
      reply.text = `The latest Dubai provider reading available in this session is ${t.toFixed(1)}°C${Number.isFinite(apparent) ? `, with an apparent temperature of ${apparent.toFixed(1)}°C` : ''}. This is city-level information, not a measurement at your exact location. For a suitable time to go outside, check HeatShield and your activity duration.`;
    } else {
      reply.text = 'I cannot confirm live Dubai conditions right now because a weather reading is unavailable in this session. HeatShield displays source-linked conditions when the provider responds.';
    }
    reply.label = 'Open HeatShield'; reply.href = '#heatshield';
  } else if (/run|walk|cycling|cycle|exercise|outside|outdoor|heat|sun|shade|safe/.test(q)) {
    reply.text = 'HeatShield considers your preferred temperature, activity, planned duration, direct sun or shade, and forecast conditions across the activity window. It helps compare available times, but it cannot guarantee safety or account for every local microclimate. Consider the latest official heat guidance for strenuous activity.';
    reply.label = 'Plan with HeatShield'; reply.href = '#heatshield';
  } else if (/plant|tree|action|volunteer|city|atlas|biodivers|greener|community|satellite|mission/.test(q)) {
    reply.text = 'LUNARIS Action includes an interactive Dubai City Opportunity Atlas with 12 candidate neighborhood concepts for urban cooling, greenery, biodiversity, water, solar and waste. You can select a location, review proposed actions, change impact assumptions and register interest. These are not confirmed planting locations or approved volunteer events; real satellite evidence and field validation are pending.';
    reply.label = 'Open Dubai Action Atlas'; reply.href = './action-atlas/';
  } else if (/energy|electric|dewa|watt|air con|aircon|appliance|bill|save power/.test(q)) {
    reply.text = 'WattFlow estimates the electricity part of a Dubai DEWA bill and models how changing appliance wattage, quantity or daily usage hours could affect kWh consumption. It is a scenario calculator, not a smart-meter reading, and excludes additional bill items.';
    reply.label = 'Open WattFlow'; reply.href = '#choices';
  } else if (/food|eat|restaurant|brand|barcode|product|carbon label/.test(q)) {
    reply.text = 'FoodPrint can identify packaged products through Open Food Facts and compare two declared, source-linked footprints if their units and boundaries align. It will not claim one brand is lower-emission without comparable evidence. Generic food-category estimates are available separately.';
    reply.label = 'Open FoodPrint'; reply.href = '#choices';
  } else if (/car|drive|transport|travel|metro|bus|miles|emission|ev|vehicle/.test(q)) {
    reply.text = 'GreenMiles compares travel modes and lets you enter fuel or electricity efficiency for specific vehicles. Some transport factors are UK proxies, not Dubai fleet measurements. Petrol, diesel and EV calculations have different accounting boundaries, so always check the units.';
    reply.label = 'Open GreenMiles'; reply.href = '#choices';
  } else if (/cafe|café|coffee|business|hotel|place|explore|where to go/.test(q)) {
    reply.text = 'Explore has a small source-attributed Dubai venue catalogue, including a café with documented practices and hotels listed in Dubai tourism sustainability awards. A listed practice is not proof that a venue has a lower carbon footprint; operating hours and availability are not live.';
    reply.label = 'Explore Dubai'; reply.href = '#explore';
  } else if (/what is lunaris|who are you|help|can you do|hello|hi lumi/.test(q)) {
    reply.text = 'I am Lumi, your built-in LUNARIS climate guide. I can explain current app weather readings when available, plan outdoor activities through HeatShield, explore more responsible choices, and guide you to Dubai Action. I am not a general-purpose AI chatbot yet, and I will not invent missing facts.';
    reply.label = 'Explore the Action Atlas'; reply.href = './action-atlas/';
  } else {
    reply.text = 'I do not have a reliable answer to that question in my current local knowledge. I can help with Dubai weather, HeatShield activity planning, FoodPrint, GreenMiles, WattFlow, environmental venues, or the Action Atlas. For broader environmental research, a sourced AI service would be needed.';
    reply.label = 'Explore the Action Atlas'; reply.href = './action-atlas/';
  }
  return reply;
}
function showLumiAnswer(question) {
  const result = lumiRespond(question);
  if (!result) return;
  const target = $('#lumi-answer');
  if (!target) return;
  target.replaceChildren();
  const title = document.createElement('strong'); title.textContent = result.title;
  const p = document.createElement('p'); p.textContent = result.text;
  target.append(title, p);
  if (result.href) {
    const link = document.createElement('a'); link.textContent = `${result.label} →`;
    link.href = result.href;
    if (result.href[0] === '#') {
      link.addEventListener('click', e => { e.preventDefault(); routeTo(result.href.slice(1)); });
    }
    target.append(link);
  }
}
function bindLumiAssistant() {
  const form = $('#lumi-ask-form');
  if (!form) return;
  form.addEventListener('submit', event => {
    event.preventDefault();
    const input = $('#lumi-question'); showLumiAnswer(input.value);
  });
  $$('[data-lumi-ask]').forEach(btn => btn.addEventListener('click', () => {
    const question = btn.dataset.lumiAsk;
    $('#lumi-question').value = question;
    showLumiAnswer(question);
  }));
}

function init() {
  const eraseButton=$('#delete-my-data');
  if (eraseButton) eraseButton.addEventListener('click',eraseGuestAndLocalData);
  bindUi();
  bindForms();
  bindLumiAssistant();
  const lumiDock = $('#dock-lumi');
  if (lumiDock) lumiDock.addEventListener('click', () => {
    routeTo('home');
    requestAnimationFrame(() => {
      const assistant = $('#lumi-assistant');
      if (!assistant) return;
      assistant.scrollIntoView({ behavior: window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth', block: 'center' });
      setTimeout(() => { const question = $('#lumi-question'); if (question) question.focus({ preventScroll: true }); }, 250);
    });
  });
  renderLumi();
  $('#dubai-time').textContent = `${formatDubaiTime()} GST`;
  setInterval(() => { $('#dubai-time').textContent = `${formatDubaiTime()} GST`; }, 60000);
  routeTo(location.hash.slice(1) || 'home');
  renderImpact();
  renderDiscover();
  if (!readJson(STORAGE.prefs)) setTimeout(openPreferences, 450);
  loadWeather();
}

init();
