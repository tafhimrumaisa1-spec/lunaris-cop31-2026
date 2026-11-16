"use strict";
const field=(id)=>document.getElementById(id);
function calculateScenario(length,width,shade){
 const area=length*width, covered=area*shade/100;
 return {area,covered};
}
function update(){const length=Number(field('length').value),width=Number(field('width').value),shade=Number(field('shade').value);
 const r=calculateScenario(length,width,shade);
 field('length-value').textContent=length+' m';field('width-value').textContent=width+' m';field('shade-value').textContent=shade+'%';
 field('footprint').textContent=r.covered.toLocaleString('en-AE',{maximumFractionDigits:0})+' m²';
 field('floor').textContent='Of '+r.area.toLocaleString('en-AE')+' m² assumed corridor area. Overlap and changing sun angle excluded.';
 field('shade-overlay').style.width=shade+'%';
}
['length','width','shade'].forEach(k=>field(k).addEventListener('input',update));update();
(async()=>{
 try{const response=await fetch('./nasa_power_metrics.json',{cache:'no-store'});if(!response.ok) return;
 const data=await response.json();if(data.source!=='NASA POWER' || data.status!=='measured_reanalysis' || !data.periods || !data.evaluation) return;
 field('data-status').textContent='NASA POWER atmosphere snapshot available';
 field('data-details').textContent='2024–2025 daily NASA POWER grid estimates near Dubai (25.2769° N, 55.2962° E). Data span: '+data.periods.range+'. Checked records: '+data.periods.observed_days+'. Grid-scale air temperature, not hyperlocal heat or satellite LST.';
 const e=data.evaluation;
 const stat=document.createElement('div');
 const entries=[['2024 summer mean daily max',data.periods.reference_summer_mean_max_c,'°C'],['2025 summer mean daily max',data.periods.test_summer_mean_max_c,'°C'],['2025 prior-day baseline MAE',e.persistence_mae_c,'°C'],['2025 year-prior-day baseline MAE',e.prior_year_mae_c,'°C']];
 entries.forEach(([label,value,unit])=>{const p=document.createElement('p');const s=document.createElement('strong');s.textContent=value===null?'N/A':value.toFixed(2)+unit;const l=document.createElement('span');l.textContent=label;p.append(s,l);stat.appendChild(p)});
 field('data-stats').replaceChildren(stat);
 }catch(err){/* No data: the honest offline state is intentionally retained. */}
})();
if(typeof module!=='undefined')module.exports={calculateScenario};