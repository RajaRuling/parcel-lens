'use strict';
const D=window.PARCEL_V2;
const $=id=>document.getElementById(id);
const fmt=(v,n=3)=>v==null?'—':Number(v).toFixed(n);
const pct=v=>v==null?'—':`${(v*100).toFixed(1)}%`;
const ci=(v,c,n=3)=>`${fmt(v,n)}${c?` [${fmt(c[0],n)}, ${fmt(c[1],n)}]`:''}`;
const nice=s=>String(s).replaceAll('_',' ');
const winner=D.frozen.winner, frozen=D.frozen.thresholds[winner];
let split='test', examples=[],renderToken=0;
const badge=verdict=>`<span class="tag ${verdict.toLowerCase().replaceAll(' ','-')}">${verdict}</span>`;
function cards(target,rows){$(target).innerHTML=rows.map(([label,value,note])=>`<article class="card"><span>${label}</span><strong>${value}</strong><span class="small">${note}</span></article>`).join('');}
function claimResult(c){
 if(c.id==='C5')return '0 real images; no interval';
 if(c.id==='C3')return `Recall ${ci(c.value.recall,c.ci95.recall)}<br>Alarms ${ci(c.value.alarms,c.ci95.alarms,1)} / 1,000 clean`;
 return ci(c.value,c.ci95);
}
$('claims-body').innerHTML=D.claims.map(c=>`<tr><td><strong>${c.id}</strong> · ${c.claim}</td><td>${claimResult(c)}</td><td>${badge(c.verdict)}</td></tr>`).join('');
const std=D.models[winner].test,shifted=D.models[winner].shift;
cards('headline',[
 ['Standard-style ROC AUC',fmt(std.auc),`95% CI ${std.ci95.auc.map(x=>fmt(x)).join('–')}`],
 ['Held-out-style ROC AUC',fmt(shifted.auc),`95% CI ${shifted.ci95.auc.map(x=>fmt(x)).join('–')}`],
 ['Real-image evidence','Untested','No real photographs evaluated']
]);
$('iteration-body').innerHTML=D.iterations.map(r=>`<tr><td>${nice(r.name)}</td><td>${fmt(r.validation.f1)}</td><td>${fmt(r.validation.auc)}</td><td>${r.best_epoch} / ${r.epochs_run}</td><td>${r.name===winner?'KEPT · final model':r.purpose==='ablation'?'Diagnostic ablation':'Dropped by validation rank'}</td></tr>`).join('');
$('iteration-story').innerHTML=`<p><strong>Validation selected ${nice(winner)}.</strong> The selection criterion was F1, then AUC, then simpler model. Each fit ran at most 160 epochs. Two diagnostic ablations were retained as evidence. The selected score temperature is ${D.iterations.find(r=>r.name===winner).temperature}; it was chosen on synthetic validation log loss.</p>`;
function svgChart(lines,{title,xTitle,yTitle,yMax=1,diagonal=false}){
 const mobile=window.innerWidth<650;
 const w=mobile?350:660,h=mobile?290:330,l=mobile?54:64,r=mobile?16:22,t=26,b=65,iw=w-l-r,ih=h-t-b;
 const X=x=>l+x*iw,Y=y=>t+ih-y/yMax*ih;
 let inner='';
 for(let i=0;i<=4;i++){
  const x=i/4,y=i*yMax/4;
  inner+=`<line x1="${l}" y1="${Y(y)}" x2="${w-r}" y2="${Y(y)}" stroke="#d7dfd9"/><text x="${l-9}" y="${Y(y)+4}" text-anchor="end" font-size="12">${fmt(y,yMax===1?2:0)}</text><text x="${X(x)}" y="${h-b+25}" text-anchor="middle" font-size="12">${fmt(x,2)}</text>`;
 }
 if(diagonal)inner+=`<path d="M${X(0)},${Y(0)} L${X(1)},${Y(1)}" stroke="#6f7d81" stroke-dasharray="5 5" fill="none"/>`;
 for(const line of lines){
  const points=line.points.filter(p=>p[0]!=null&&p[1]!=null);
  inner+=`<path d="${points.map((p,i)=>`${i?'L':'M'}${X(p[0])},${Y(p[1])}`).join(' ')}" fill="none" stroke="${line.color}" stroke-width="3"/>`;
  if(points.length<15)inner+=points.map(p=>`<circle cx="${X(p[0])}" cy="${Y(p[1])}" r="4" fill="${line.color}"/>`).join('');
 }
 return `<svg class="chart" viewBox="0 0 ${w} ${h}" role="img" aria-label="${title}"><title>${title}</title><g font-family="system-ui" fill="#233c43">${inner}<text x="${l+iw/2}" y="${h-12}" text-anchor="middle" font-size="13">${xTitle}</text><text transform="translate(17 ${t+ih/2}) rotate(-90)" text-anchor="middle" font-size="13">${yTitle}</text></g></svg>`;
}
function renderSplit(){
 const m=D.models[winner][split];
 $('model-body').innerHTML=Object.entries(D.models).map(([name,parts])=>{const r=parts[split];return `<tr class="${name===winner?'selected':''}"><td>${nice(name)}${name===winner?' · selected':''}</td><td>${pct(r.precision)}</td><td>${pct(r.recall)}</td><td>${fmt(r.f1)}</td><td>${ci(r.auc,r.ci95.auc)}</td><td>${fmt(r.average_precision)}</td><td>${fmt(r.brier)}</td></tr>`;}).join('');
 const cm=m.confusion;
 $('matrix').innerHTML=`<div class="matrix-grid">${[['tn','Clean → clear'],['fp','Clean → review'],['fn','Damaged → clear'],['tp','Damaged → review']].map(([k,label])=>`<div class="matrix-cell ${['fp','fn'].includes(k)?'bad':''}">${label}<strong>${cm[k]}</strong></div>`).join('')}</div>`;
 $('matrix-note').textContent=`Rows above name true class → simulated action. ${m.n} independent scenes; fixed threshold ${fmt(frozen,6)}.`;
 $('calibration').innerHTML=svgChart([{color:'#155343',points:m.calibration.filter(b=>b.n).map(b=>[b.score,b.observed])}],{title:'Reliability: predicted score versus observed damaged share in ten bins',xTitle:'Mean image score',yTitle:'Observed damaged share',diagonal:true});
 $('calibration-note').textContent=`Brier ${ci(m.brier,m.ci95.brier)}; ECE ${ci(m.ece,m.ci95.ece)}. Ten equal-width score bins; empty bins omitted. Dashed diagonal means perfect calibration at this synthetic prevalence.`;
 $('frozen-note').textContent=`Frozen review threshold: ${fmt(frozen,6)}. On ${split==='test'?'standard':'shifted'} scenes it triggers ${fmt(m.clean_alarms_per_1000,1)} false reviews per 1,000 clean images and misses ${fmt(m.damage_misses_per_1000,1)} per 1,000 damaged images. Lower scores are simulated clears; real auto-clear is disabled.`;
 const curve=D.threshold_curves[split].filter(r=>r.threshold>=0&&r.threshold<=1).sort((a,b)=>a.threshold-b.threshold);
 $('curves').innerHTML=svgChart([
  {color:'#155343',points:curve.map(r=>[r.threshold,r.recall])},
  {color:'#a84717',points:curve.map(r=>[r.threshold,r.clean_alarms_per_1000/1000])}
 ],{title:'Threshold sensitivity: recall and clean false alarm fraction',xTitle:'Review threshold',yTitle:'Fraction of images'})+'<p class="chart-legend"><span class="legend-a">● Damage recall</span> &nbsp; <span class="legend-b">● Clean false-alarm fraction</span></p>';
 $('workload').innerHTML=D.operational[split].map(r=>`<tr><td>${pct(r.assumed_prevalence)}</td><td>${fmt(r.false_reviews_per_1000,1)}</td><td>${fmt(r.missed_damage_per_1000,1)}</td><td>${fmt(r.reviews_per_1000,1)}</td></tr>`).join('');
 $('subgroup-body').innerHTML=Object.entries(D.subgroups[split]).flatMap(([field,values])=>Object.entries(values).map(([name,r])=>`<tr><td>${nice(field)}</td><td>${nice(name)}</td><td>${r.n}</td><td>${ci(r.recall,r.ci95.recall)}</td><td>${ci(r.clean_alarms_per_1000,r.ci95.clean_alarms_per_1000,1)}</td></tr>`)).join('');
 examples=D.examples.filter(r=>r.split===split);
 $('example').innerHTML=examples.map((r,i)=>`<option value="${i}">${r.id} · ${nice(r.label)}${r.review!==Boolean(r.damaged)?' · ERROR':''}</option>`).join('');
 renderDecision();renderExample();
}
function renderDecision(){
 const t=Number($('threshold').value);$('threshold-value').value=fmt(t,2);
 const r=D.threshold_curves[split].reduce((best,row)=>Math.abs(row.threshold-t)<Math.abs(best.threshold-t)?row:best);
 cards('decision-cards',[
 ['Damage recall',pct(r.recall),`At sensitivity threshold ${fmt(r.threshold,2)}`],
 ['False reviews',fmt(r.clean_alarms_per_1000,1),'Per 1,000 clean images'],
 ['Damage missed',fmt(r.damage_misses_per_1000,1),'Per 1,000 damaged images']
 ]);
}
function renderExample(){
 const r=examples[Number($('example').value)||0];if(!r)return;
 const token=++renderToken;
 const isError=r.review!==Boolean(r.damaged);
 $('verdict').className=`tag ${isError?'not-supported':'supported'}`;
 $('verdict').textContent=r.review?'SIMULATED REVIEW':'SIMULATED CLEAR';
 $('scene-title').textContent=`${nice(r.label)} · score ${fmt(r.score)}`;
 $('details').textContent=`${r.id} · ${r.lighting} lighting · ${r.severity} severity · ${r.tape_occlusion?'extra tape occlusion':'no extra tape occlusion'}. Ground truth: ${r.damaged?'damaged':'clean'}. Frozen threshold ${fmt(frozen,6)}.`;
 $('error-explanation').textContent=isError?(r.damaged?'MISSED DAMAGE. The frozen model would clear this generated damaged scene. A clean-looking or partially hidden patch cannot establish safety.':'FALSE ALARM. The frozen model sends this generated clean scene for review. Tape, printing, shading and backgrounds are possible confounders; the cause has not been independently verified.'):'Control example: the simulated decision agrees with the generator label. Agreement on this drawing does not establish accuracy on a real photograph.';
 const image=new Image();image.onload=()=>{if(token!==renderToken)return;
  const canvas=$('scene'),ctx=canvas.getContext('2d');ctx.clearRect(0,0,canvas.width,canvas.height);ctx.drawImage(image,0,0,canvas.width,canvas.height);
  if($('show-truth').checked){ctx.strokeStyle='#c0005a';ctx.lineWidth=5;for(const obj of r.objects){const [x0,y0,x1,y1]=obj.box;ctx.strokeRect(x0*3,y0*3,(x1-x0)*3,(y1-y0)*3);}}
  canvas.dataset.rendered=r.id;canvas.setAttribute('aria-label',`${r.id}: synthetic ${nice(r.label)} parcel, ${r.review?'review':'clear'} decision${isError?', classification error':''}`);
 };image.onerror=()=>{$('details').textContent+=' Image unavailable.';};image.src=r.image;
}
$('split').addEventListener('change',()=>{split=$('split').value;renderSplit();});
$('example').addEventListener('change',renderExample);
$('show-truth').addEventListener('change',renderExample);
$('threshold').addEventListener('input',renderDecision);
$('previous').addEventListener('click',()=>{const n=examples.length;$('example').value=String((Number($('example').value)+n-1)%n);renderExample();});
$('next').addEventListener('click',()=>{$('example').value=String((Number($('example').value)+1)%examples.length);renderExample();});
renderSplit();
