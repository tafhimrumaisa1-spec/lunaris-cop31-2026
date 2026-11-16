'use strict';
const API = (window.LUNARIS_API_BASE || '').replace(/\/$/, '');
const DEFAULTS = {
 greening:{unit_benefit:12,unit_cost:1400,survival:.70,unit_benefit_label:'m² mature canopy / surviving tree',impact_unit:'m²',impact_metric:'potential mature canopy',note:'Canopy footprint only, NOT a cooling-temperature claim.'},
 biodiversity:{unit_benefit:1,unit_cost:50,survival:.70,unit_benefit_label:'m² habitat / converted m²',impact_unit:'m²',impact_metric:'potential established native habitat',note:'Not a measured biodiversity increase.'},
 mobility:{unit_benefit:1.8,unit_cost:2400,survival:1,unit_benefit_label:'assumed shade width (m)',impact_unit:'m²',impact_metric:'potential shade footprint',note:'Not a modeled air temperature reduction.'},
 solar:{unit_benefit:1550,unit_cost:4000,survival:1,unit_benefit_label:'annual kWh / installed kWp',impact_unit:'kWh/year',impact_metric:'illustrative annual electricity generation',note:'Not a verified roof or emissions saving.'},
 waste:{unit_benefit:3,unit_cost:200,survival:.50,unit_benefit_label:'kg diverted / participant / month',impact_unit:'kg/month',impact_metric:'hypothetical waste diversion',note:'Requires a licensed partner and measured material flows.'},
 water:{unit_benefit:12,unit_cost:650,survival:.80,unit_benefit_label:'liters saved / day / point',impact_unit:'liters/day',impact_metric:'hypothetical water saving',note:'Requires metered pre/post validation.'}
};
// Mirrors server catalogue to keep map useful when backend is offline. All are concepts, not evidence-based detections.
const IDEAS = [
 ['marina-shade','Dubai Marina',25.0801,55.1404,'greening','Investigate pedestrian shade corridors','candidate trees',12,'Study shade continuity on pedestrian routes; compare trees and low-water shade structures.'],
 ['jbr-cooling','Jumeirah Beach Residence',25.0771,55.1312,'mobility','Explore lower-exposure walking links','metres of proposed shade',200,'Investigate shaded access to outdoor destinations and transit.'],
 ['jlt-biodiversity','Jumeirah Lakes Towers',25.0663,55.1412,'biodiversity','Explore native habitat connectors','m² of candidate habitat',300,'Explore native species links between existing landscape areas.'],
 ['downtown-cooling','Downtown Dubai',25.1923,55.2814,'mobility','Investigate shaded pedestrian transfers','metres of proposed shade',250,'Evaluate shade continuity and accessible outdoor transfers.'],
 ['business-bay-solar','Business Bay',25.1853,55.2708,'solar','Study shared-building rooftop solar','kWp of hypothetical solar capacity',35,'Screen representative roofs for further structural and utility review.'],
 ['deira-waste','Deira',25.2701,55.3075,'waste','Investigate neighborhood waste sorting','participating households',100,'Study a sorting and collection pilot with licensed local partners.'],
 ['bur-dubai-green','Bur Dubai',25.26,55.2933,'greening','Study low-water street greening','candidate trees',16,'Identify routes for shade investigation while protecting historic fabric.'],
 ['al-quoz-materials','Al Quoz',25.1447,55.2352,'waste','Explore reuse and material recovery','participating businesses',20,'Investigate business partners and documented material recovery.'],
 ['barsha-water','Al Barsha',25.1063,55.2054,'water','Evaluate landscape water efficiency','candidate irrigation points',20,'Review irrigation settings with land managers and field checks.'],
 ['silicon-oasis-solar','Dubai Silicon Oasis',25.1249,55.3782,'solar','Screen institutional solar potential','kWp of hypothetical solar capacity',50,'Investigate consenting institutional roofs and site restrictions.'],
 ['international-city-greening','International City',25.1657,55.404,'greening','Identify candidate shade gaps','candidate trees',25,'Study shading of established pedestrian corridors.'],
 ['creek-biodiversity','Dubai Creek Harbour',25.2057,55.3471,'biodiversity','Assess ecological connectivity','m² of candidate habitat',500,'Research biodiversity opportunities without altering protected habitats.']
].map(([id,name,lat,lng,category,title,unit,quantity,detail])=>({id,name,lat,lng,category,title,unit,quantity,detail,
 checks:['Field survey and independent evidence','Landowner and municipality approvals','Resource demand and long-term maintenance'],
 policy:{label:'Dubai 2040 / related sustainability strategy',url:'https://www.dm.gov.ae/municipality-business/planning-and-construction/dubai-2040-urban-master-plan/',sdgs:category==='solar'?['7','13']:category==='water'?['6','11']:['11','13','15']}}));
let areas=IDEAS, selected='marina-shade', filter='all', map=null, markers=new Map(), sessionToken=null;
const $=q=>document.querySelector(q);
const escapeText=s=>String(s||'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const names={all:'All',greening:'Greenery',biodiversity:'Biodiversity',mobility:'Urban cooling',solar:'Clean energy',water:'Water',waste:'Waste'};
const nfmt=(v, digits=0)=>Number(v).toLocaleString('en-AE',{maximumFractionDigits:digits});
async function getAtlas(){try{const res=await fetch(API+'/v1/action/atlas',{signal:AbortSignal.timeout(5000)});if(!res.ok)throw Error('Unavailable');const data=await res.json();if(Array.isArray(data.opportunities)&&data.opportunities.length)areas=data.opportunities;}catch(e){console.info('Atlas offline: labeled concept catalogue in use.');}}
function renderFilters(){const node=$('#filters');node.innerHTML=Object.entries(names).map(([id,label])=>`<button class="filter ${filter===id?'selected':''}" data-filter="${id}" aria-pressed="${filter===id}">${label}</button>`).join('');node.querySelectorAll('[data-filter]').forEach(b=>b.onclick=()=>{filter=b.dataset.filter;render();});}
function visible(){return areas.filter(a=>filter==='all'||a.category===filter)}
function renderList(){const list=visible();$('#map-count').textContent=list.length+' area concepts';$('#rail-count').textContent=list.length+' AREAS';$('#opportunity-list').innerHTML=list.map((a,i)=>`<button class="op-row ${a.id===selected?'selected':''}" data-id="${escapeText(a.id)}"><span class="op-number">${String(i+1).padStart(2,'0')}</span><span class="op-copy"><span class="op-category">${escapeText(names[a.category])} / REVIEW NEEDED</span><strong>${escapeText(a.title)}</strong><small>${escapeText(a.name)} · illustration only</small></span><span class="op-arrow">↗</span></button>`).join('');document.querySelectorAll('.op-row').forEach(b=>b.onclick=()=>selectArea(b.dataset.id));}
function buildMap(){if(window.L&&$('#map')){map=L.map('map',{zoomControl:false,scrollWheelZoom:false}).setView([25.165,55.272],10);L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png',{attribution:'© OpenStreetMap contributors',maxZoom:18}).addTo(map);L.control.zoom({position:'topright'}).addTo(map);renderMarkers();}
 else{document.querySelector('#map').hidden=true;document.querySelector('#map-fallback').hidden=false;renderMarkers();}}
function renderMarkers(){markers.forEach(m=>m.remove?.());markers.clear();const list=visible();if(map){list.forEach(a=>{const icon=L.divIcon({className:'',html:`<span class="city-pin ${a.id===selected?'active':''}">✦</span>`,iconSize:[30,30],iconAnchor:[15,15]});const m=L.marker([a.lat,a.lng],{icon}).addTo(map).on('click',()=>selectArea(a.id));markers.set(a.id,m);});}else{const fallback=$('#fallback-pins');fallback.innerHTML='';list.forEach(a=>{const x=7+(a.lng-55.10)/(55.43-55.10)*87;const y=86-(a.lat-25.04)/(25.31-25.04)*76;const b=document.createElement('button');b.className='fallback-pin';b.style.left=x+'%';b.style.top=y+'%';b.title=a.name;b.setAttribute('aria-label',a.name);b.onclick=()=>selectArea(a.id);fallback.appendChild(b);});}}
function selectArea(id){const a=areas.find(x=>x.id===id);if(!a)return;selected=id;filter=filter!=='all'&&filter!==a.category?'all':filter;render();$('#case-area').textContent=a.name.toUpperCase()+' / DUBAI';$('#case-title').innerHTML=escapeText(a.title).replace(/ (\S+)$/,'<br><em>$1</em>');$('#case-detail').textContent=a.detail;$('#case-checks').innerHTML=a.checks.map(c=>`<li>${escapeText(c)}</li>`).join('');$('#policy-link').textContent=a.policy.label+' ↗';$('#policy-link').href=a.policy.url;$('#sdg-chips').textContent='SDG '+a.policy.sdgs.join(' · ');const d=DEFAULTS[a.category];$('#quantity-label').textContent=a.unit;$('#quantity').value=a.quantity;$('#benefit-label').textContent=d.unit_benefit_label;$('#benefit').value=d.unit_benefit;$('#adoption').value=Math.round(d.survival*100);refreshScenario();if(map){map.flyTo([a.lat,a.lng],a.category==='waste'?12:13,{duration:.6});}if(document.activeElement?.classList.contains('op-row'))$('#case').scrollIntoView({behavior:'smooth'});}
function render(){renderFilters();renderList();renderMarkers();}
function refreshScenario(){const a=areas.find(x=>x.id===selected);if(!a)return;const d=DEFAULTS[a.category];const quantity=Number($('#quantity').value),benefit=Number($('#benefit').value),adoption=Number($('#adoption').value)/100;
$('#adoption-value').textContent=Math.round(adoption*100)+'%';const valid=[quantity,benefit,adoption].every(Number.isFinite)&&quantity>=0&&quantity<=100000&&benefit>=0&&adoption>=0&&adoption<=1;
$('#impact-value').textContent=valid?nfmt(quantity*benefit*adoption,2):'Invalid inputs';$('#impact-unit').textContent=d.impact_unit+' / '+d.impact_metric;$('#budget-value').textContent=valid?'AED '+nfmt(quantity*d.unit_cost):'—';$('#impact-note').textContent=d.note+' Calculated from adjustable assumptions, not measured site data.';}
async function ensureSession(){if(sessionToken)return sessionToken;const saved=sessionStorage.getItem('lunaris.atlas.guest_token');if(saved){sessionToken=saved;return saved;}const response=await fetch(API+'/v1/session',{method:'POST',headers:{'Content-Type':'application/json'}});if(!response.ok)throw Error('Guest session unavailable');const session=await response.json();if(!session.session_token)throw Error('Invalid session response');sessionToken=session.session_token;sessionStorage.setItem('lunaris.atlas.guest_token',sessionToken);return sessionToken;}
async function join(){const area=areas.find(x=>x.id===selected);const output=$('#interest-result');if(!$('#consent').checked){output.textContent='Please confirm you understand this is only concept-stage interest.';return;}output.textContent='Recording interest…';try{const token=await ensureSession();const response=await fetch(API+'/v1/action/atlas/'+encodeURIComponent(area.id)+'/interest',{method:'POST',headers:{'Content-Type':'application/json',Authorization:'Bearer '+token},body:JSON.stringify({consent:true})});const data=await response.json();if(!response.ok){if(response.status===409){output.textContent='Interest was already recorded for your guest session. No organizer is notified.';return;}throw Error(data.detail||'Unavailable');}output.textContent=data.notice||'Interest recorded as a demo concept. No organizer was notified.';}
catch(e){const key='lunaris.atlas.local-interest.v1';try{const old=JSON.parse(localStorage.getItem(key)||'[]');if(!old.includes(area.id))localStorage.setItem(key,JSON.stringify([...old,area.id]));output.textContent='Saved interest locally on this device only. No signup, organizer notification or event enrollment has occurred.';}catch{output.textContent='Could not store interest. Please retry on a supported browser.';}}}
function downloadBrief(){const a=areas.find(x=>x.id===selected);const d=DEFAULTS[a.category];const q=Number($('#quantity').value),b=Number($('#benefit').value),r=Number($('#adoption').value)/100;const lines=[
 'LUNARIS ACTION / CITY OPPORTUNITY ATLAS','AREA: '+a.name,'CATEGORY: '+a.category,'CONCEPT: '+a.title,'STATUS: HYPOTHETICAL AREA INVESTIGATION ONLY','',
 'Concept: '+a.detail,'', 'Action needed before implementation:',...a.checks.map(x=>'- '+x),'',
 'Illustrative scenario assumptions:','Quantity: '+q+' '+a.unit,'Unit benefit: '+b+' '+d.unit_benefit_label,'Implementation/survival fraction: '+r,'Potential output: '+(q*b*r).toFixed(2)+' '+d.impact_unit,
 'Illustrative budget: AED '+(q*d.unit_cost).toFixed(2),'',
 'IMPORTANT: These quantities do NOT represent satellite detections, verified planting sites, approved projects, measured environmental benefit, or actual volunteers.','Policy reference: '+a.policy.url,
 'Suggested data: Dynamic World, Sentinel-2, Landsat surface temperature, OSM; site validation essential.'
 ];const blob=new Blob([lines.join('\n')],{type:'text/plain;charset=utf-8'});const href=URL.createObjectURL(blob);const link=document.createElement('a');link.href=href;link.download='lunaris-action-'+a.id+'.txt';link.click();URL.revokeObjectURL(href);}

// Reviewed environmental data is explicitly distinct from conceptual actions and impacts.
async function loadEvidence() {
 const status=$('#satellite-evidence-text');const list=$('#satellite-evidence-list');
 if (!status || !list) return;
 try {
   const response=await fetch(API+'/v1/action/atlas/evidence',{signal:AbortSignal.timeout(5000)});
   if (!response.ok) throw Error('Evidence API unavailable');
   const result=await response.json();
   if (result.status!=='reviewed_area_indicators') {status.textContent=result.message || 'No reviewed observations installed; all opportunities remain conceptual.';return;}
   const current=$('#atlas-current-status');if(current)current.textContent='CURRENT DATA STATUS: REVIEWED NEIGHBORHOOD INDICATORS · CONCEPT OPPORTUNITIES';
   status.textContent='Reviewed satellite-area summaries are available for the listed neighborhood study circles. These do not establish a suitable intervention site or predicted impact. Period: '+(result.source?.dataset_period||'unspecified');
   const values=result.indicators.filter(x=>x.lst_c!==null || x.trees!==null).slice(0,12);
   list.replaceChildren();
   values.forEach(x=>{
     const area=areas.find(a=>a.id===x.area_id); if (!area) return;
     const item=document.createElement('div');
     const heading=document.createElement('dt');heading.textContent=area.name;
     const detail=document.createElement('dd');
     detail.textContent=[Number.isFinite(x.trees)?'Mean tree probability '+Math.round(x.trees*100)+'%':null,Number.isFinite(x.ndvi)?'Median NDVI '+x.ndvi.toFixed(2):null,Number.isFinite(x.lst_c)?'Median Landsat LST '+x.lst_c.toFixed(1)+'°C':null].filter(Boolean).join(' · ') || 'No suitable measurements';
     item.append(heading,detail);list.append(item);
   });
 } catch {status.textContent='Satellite review data unavailable. No environmental measurements have been inferred.';}
}
async function start(){await getAtlas();loadEvidence();renderFilters();renderList();buildMap();selectArea(selected);$('#quantity').addEventListener('input',refreshScenario);$('#benefit').addEventListener('input',refreshScenario);$('#adoption').addEventListener('input',refreshScenario);$('#download-button').addEventListener('click',downloadBrief);$('#join-button').addEventListener('click',()=>{$('#interest-target').textContent=areas.find(a=>a.id===selected).title+' — '+areas.find(a=>a.id===selected).name;$('#consent').checked=false;$('#interest-result').textContent='';$('#interest-dialog').showModal();});$('#interest-form').addEventListener('submit',e=>{e.preventDefault();join();});}
start();
