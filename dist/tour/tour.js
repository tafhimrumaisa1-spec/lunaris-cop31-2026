const steps = [
  { kicker:'00 / THE MISSION', title:'One planet. Three intelligences.', body:'LUNARIS connects personal climate adaptation, sustainable everyday decisions, and city-scale environmental opportunity. Lumi helps visitors navigate them; the Action Network provides a pathway for participation.', cta:'Explore the three-layer architecture', href:'/#intelligence-map', tag:'THREE LAYERS / ONE PLATFORM', caveat:'This is a connected product vision, not a claim that every feature automatically shares live data.' },
  { kicker:'01 / PERSONAL INTELLIGENCE', title:'Understand the day you are stepping into.', body:'HeatShield compares forecast-based activity windows against duration and exposure preferences. Its construction-worker extension explains UAE heat-work rules in English, Bangla and Arabic.', cta:'Open HeatShield', href:'/app/#heatshield', tag:'HEATSHIELD / WORKER HEAT', caveat:'Forecast-based planning and policy information; not personalized medical clearance or live SMS alerts.' },
  { kicker:'02 / CHOICES', title:'Turn good intentions into trade-offs.', body:'GreenMiles compares transport choices; FoodPrint supports ingredient and product exploration and links to Fridge Brain. WattFlow evaluates household energy scenarios and links to a climate-resilience self-check.', cta:'Explore Choices', href:'/app/#choices', tag:'GREENMILES / FOODPRINT / WATTFLOW', caveat:'Emissions factors and environmental estimates depend on their stated sources and assumptions.' },
  { kicker:'03 / WALLET', title:'Save money. Understand emissions.', body:'Carbon & Cost Wallet makes a manual, transparent comparison of commute costs and estimated operational emissions, showing AED and CO₂e differences together.', cta:'Open Carbon & Cost Wallet', href:'/app/wallet/', tag:'MONEY + CLIMATE', caveat:'No bank connection or transaction access; some emissions factors are non-UAE proxies.' },
  { kicker:'04 / HOME & FOOD', title:'Adapt at home. Waste less food.', body:'Fridge Brain prioritizes user-entered ingredients and dates; Home Resilience examines shade, overheating, water entry and electrical concerns. Climate Insurance introduces questions to ask about potential coverage.', cta:'Open Fridge Brain', href:'/app/foodprint-fridge/', tag:'FRIDGE / HOME / INSURANCE', caveat:'No camera recognition, automated building inspection, food-safety assessment or insurance quotes.' },
  { kicker:'05 / CITY INTELLIGENCE', title:'See your city as a place to improve.', body:'The Dubai Action Atlas displays curated neighborhood opportunity concepts spanning cooling, greenery, biodiversity and resource efficiency. It is a starting point for investigation rather than a map of verified interventions.', cta:'Open Dubai Action Atlas', href:'/app/action-atlas/', tag:'NEIGHBORHOODS / OPPORTUNITIES', caveat:'Neighborhood proposals are not independently confirmed satellite-detected project sites.' },
  { kicker:'06 / ACTION STUDIO', title:'Move from a concern to a scenario.', body:'Explore an illustrative shade-corridor scenario and adjust assumptions. Compare the hypothetical intervention area before interpreting any benefit; evidence and uncertainty remain visible.', cta:'Open Action & Resilience Lab', href:'/app/cop31-lab/', tag:'SCENARIOS / EVIDENCE', caveat:'The calculator does not predict measured temperature reductions.' },
  { kicker:'07 / THE RESEARCH', title:'Discover Dubai’s thermal paradox.', body:'The research case cites published findings about daytime and nighttime urban heat. A reproducible NASA POWER pipeline evaluates coarse atmospheric estimates and simple baselines; the page shows metrics only when a validated snapshot is bundled.', cta:'Read the Dubai case study', href:'/app/action-atlas/dubai-heat-case/', tag:'DUBAI / HEAT STUDY', caveat:'Published research is not a measurement by LUNARIS, and NASA POWER is not street-level surface temperature.' },
  { kicker:'08 / MEET LUMI', title:'Ask better environmental questions.', body:'Lumi combines secure server-side Groq conversation with an explicit allowlist of LUNARIS evidence tools. When Groq or a data provider is unavailable, the bounded local guide labels the fallback instead of inventing an answer.', cta:'Open Lumi', href:'/app/#home', tag:'LUMI / GUIDED EXPLANATIONS', caveat:'Never present unavailable tool outputs, comfort rankings or unverified predictions as facts or medical guidance.' },
  { kicker:'09 / FROM INSIGHT TO ACTION', title:'Let intelligence lead somewhere.', body:'The complete journey connects climate awareness, personal and household decisions, neighborhood evidence and interest in collective action. Next: validate local conditions and evaluate interventions with real participants.', cta:'Explore community Action', href:'/app/action-atlas/', tag:'UNDERSTAND → DECIDE → PARTICIPATE', caveat:'Expressions of interest are not completed environmental interventions or verified impact.' }
];

let active = 0;
const $ = selector => document.querySelector(selector);
const menu = $('#step-menu');

steps.forEach((step, index) => {
  const button = document.createElement('button');
  button.className = 'step';
  button.type = 'button';
  const number = document.createElement('small');
  number.textContent = step.kicker.split(' / ')[0];
  const name = document.createElement('span');
  name.className = 'step-name';
  name.textContent = step.title;
  button.append(number, name);
  button.addEventListener('click', () => select(index));
  menu.append(button);
});

function select(index) {
  active = Math.max(0, Math.min(steps.length - 1, index));
  const step = steps[active];
  document.querySelectorAll('.step').forEach((element, item) => {
    if (item === active) element.setAttribute('aria-current', 'step');
    else element.removeAttribute('aria-current');
  });
  $('#kicker').textContent = step.kicker;
  $('#step-title').textContent = step.title;
  $('#description').textContent = step.body;
  $('#tag').textContent = step.tag;
  $('#caveat').textContent = step.caveat;
  $('#go').textContent = step.cta + ' ↗';
  $('#go').href = step.href;
  $('#counter').textContent = String(active + 1).padStart(2, '0') + ' / ' + String(steps.length).padStart(2, '0');
  $('#progress').style.width = ((active + 1) / steps.length * 100) + '%';
  $('#prev').disabled = active === 0;
  $('#next').textContent = active === steps.length - 1 ? 'Start again ↺' : 'Next →';
  history.replaceState(null, '', '#step-' + (active + 1));
}

$('#prev').addEventListener('click', () => select(active - 1));
$('#next').addEventListener('click', () => select(active === steps.length - 1 ? 0 : active + 1));
document.addEventListener('keydown', event => {
  if (['INPUT', 'TEXTAREA', 'SELECT'].includes(document.activeElement.tagName)) return;
  if (event.key === 'ArrowRight') select(active + 1);
  if (event.key === 'ArrowLeft') select(active - 1);
});
const hash = location.hash.match(/^#step-(\d+)$/);
select(hash ? Number(hash[1]) - 1 : 0);
