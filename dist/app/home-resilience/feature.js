'use strict';
const $=id=>document.getElementById(id);
const esc=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const homeGuidance=[
 ['home-heat','Ask the building manager about overheating mitigation and ventilation; avoid unverified cooling claims.'],
 ['home-shade','Investigate removable shading or curtains suitable for your tenancy and building rules.'],
 ['home-water','Document previous water entry and request a property drainage and waterproofing inspection.'],
 ['home-drains','Ask for a drainage inspection and maintenance, especially before heavy rain.'],
 ['home-power','Ask a qualified electrician to assess any electrical outlet exposed to water; do not modify wiring yourself.']
];
$('home-form').addEventListener('submit',e=>{e.preventDefault();let items=homeGuidance.map(([id,msg])=>({risk:Number($(id).value),msg})).filter(x=>x.risk>0).sort((a,b)=>b.risk-a.risk);const score=homeGuidance.reduce((sum,[id])=>sum+Number($(id).value),0);$('home-headline').textContent=score===0?'No concerns reported in this quick checklist.':`${items.length} area${items.length>1?'s':''} to investigate.`;$('home-recommendations').innerHTML=(items.length?items:[{msg:'Continue routine maintenance and periodic checks; this checklist does not confirm that the home is climate-proof.'}]).map(x=>'<li>'+esc(x.msg)+'</li>').join('');});
