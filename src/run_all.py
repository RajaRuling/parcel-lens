"""One-command frozen protocol: render, validate, freeze, evaluate and build site."""
import os
for name in ['OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS']:os.environ[name]='1'
import hashlib
import json
from pathlib import Path
import numpy as np
from PIL import Image
from .procedural import generate
from .learned import Head,features,logloss
from .statistics import metrics,with_ci,paired_difference,select_threshold,verdict
from .detector import detect

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'data/v2'

def dump(path,value):path.write_text(json.dumps(value,indent=2,allow_nan=False)+'\n')
def matrix(records,normalize=True):
    rows=[]
    for record in records:
        with Image.open(DATA/record['file']) as im:rows.append(features(im,normalize=normalize))
    return np.array(rows)
def classical(records):
    scores=[]
    for record in records:
        with Image.open(DATA/record['file']) as im:scores.append(float(bool(detect(im))))
    return np.array(scores)

def main():
    DATA.mkdir(parents=True,exist_ok=True);models=DATA/'models';models.mkdir(exist_ok=True)
    print('Render 4,800 independent scenes',flush=True);records=generate(DATA)
    train=[r for r in records if r['split']=='train'];val=[r for r in records if r['split']=='validation']
    print('Extract training and validation features only',flush=True)
    x=matrix(train);xv=matrix(val);y=np.array([r['damaged'] for r in train]);yv=np.array([r['damaged'] for r in val])
    trials=[];heads={};validation={}
    for hidden in [0,32]:
        for reg in [0.001,0.01]:
            name=f'{"neural32" if hidden else "linear"}_r{reg}'
            print('Fit',name,flush=True);head=Head(hidden,reg).fit(x,y,xv,yv);p=head.predict(xv);summary=select_threshold(yv,p)
            head.save(models/(name+'.npz'));heads[name]=(head,'full');validation[name]=(p,summary)
            trials.append({'name':name,'purpose':'candidate','hidden':hidden,'regularization':reg,'best_epoch':head.best_epoch,
                'epochs_run':len(head.history),'seconds':head.fit_seconds,'temperature':head.temperature,'validation_loss':logloss(yv,p),
                'validation':summary,'history':head.history})
    winner=max(validation,key=lambda k:(validation[k][1]['f1'],validation[k][1]['auc'],-heads[k][0].hidden))
    print('Validation winner frozen:',winner,flush=True)
    for name,mode,xt,xvt in [('ablate_spatial','global',x[:,:12],xv[:,:12]),('ablate_normalization','raw',matrix(train,False),matrix(val,False))]:
        selected=heads[winner][0];head=Head(selected.hidden,selected.regularization).fit(xt,y,xvt,yv);p=head.predict(xvt);summary=select_threshold(yv,p)
        head.save(models/(name+'.npz'));heads[name]=(head,mode);validation[name]=(p,summary)
        trials.append({'name':name,'purpose':'ablation','best_epoch':head.best_epoch,'epochs_run':len(head.history),'seconds':head.fit_seconds,
            'temperature':head.temperature,'validation_loss':logloss(yv,p),'validation':summary,'history':head.history})
    for name in ['always_review','classical']:
        p=np.ones(len(val)) if name=='always_review' else classical(val)
        # Preserve the classical operating rule; do not turn it into always-review by threshold tuning.
        validation[name]=(p,metrics(yv,p,0.5))
    frozen={'winner':winner,'thresholds':{name:float(result[1]['threshold']) for name,result in validation.items()},
        'selection':'validation F1, then AUC, then simpler head','seed':20261029,'bootstrap_resamples':1000,
        'plan_sha256':hashlib.sha256((ROOT/'EXPERIMENTS.md').read_bytes()).hexdigest(),
        'model_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(models.glob('*.npz'))}}
    dump(DATA/'frozen.json',frozen);dump(DATA/'iterations.json',trials)
    write_iterations(trials,winner)
    results={'schema':2,'real_images':0,'synthetic_images':len(records),'splits':{s:sum(r['split']==s for r in records) for s in ['train','validation','test','shift']},
        'frozen':frozen,'models':{},'iterations':[{k:v for k,v in row.items() if k!='history'} for row in trials], 'test_records':[],'subgroups':{}}
    for split in ['test','shift']:
        print('Final frozen evaluation:',split,flush=True);part=[r for r in records if r['split']==split]
        xp=matrix(part);raw=matrix(part,False);yt=np.array([r['damaged'] for r in part]);predictions={}
        for name,(head,mode) in heads.items():predictions[name]=head.predict(xp if mode=='full' else xp[:,:12] if mode=='global' else raw)
        predictions['always_review']=np.ones(len(part));predictions['classical']=classical(part)
        for name,p in predictions.items():
            print('Intervals',split,name,flush=True)
            results['models'].setdefault(name,{})[split]=with_ci(yt,p,frozen['thresholds'][name])
        p=predictions[winner];threshold=frozen['thresholds'][winner]
        results['subgroups'][split]={}
        for field in ['label','severity','lighting','tape_occlusion']:
            out={}
            for value in sorted(set(str(r[field]) for r in part)):
                idx=np.array([str(r[field])==value for r in part]);out[value]=with_ci(yt[idx],p[idx],threshold)
            results['subgroups'][split][field]=out
        results.setdefault('paired',{})[split]=paired_difference(yt,p,predictions['classical'],threshold,0.5)
        results.setdefault('threshold_curves',{})[split]=[metrics(yt,p,float(t)) for t in np.r_[np.linspace(0,1,21),threshold]]
        for i,r in enumerate(part):
            r=dict(r);r['score']=float(p[i]);r['review']=bool(p[i]>=threshold);r['classical_score']=float(predictions['classical'][i]);results['test_records'].append(r)
    standard=results['models'][winner]['test'];shift=results['models'][winner]['shift'];delta=results['paired']['test']
    safety=[verdict(standard['recall'],standard['ci95']['recall'],0.9),verdict(standard['clean_alarms_per_1000'],standard['ci95']['clean_alarms_per_1000'],100,False)]
    results['claims']=[
        {'id':'C1','claim':'Standard-style damage ROC AUC >= 0.80','value':standard['auc'],'ci95':standard['ci95']['auc'],'verdict':verdict(standard['auc'],standard['ci95']['auc'],0.8)},
        {'id':'C2','claim':'F1 improvement over classical >= 0.05','value':delta['value'],'ci95':delta['ci95'],'verdict':verdict(delta['value'],delta['ci95'],0.05)},
        {'id':'C3','claim':'Recall >= 0.90 and <=100 alarms / 1,000 clean','value':{'recall':standard['recall'],'alarms':standard['clean_alarms_per_1000']},'ci95':{'recall':standard['ci95']['recall'],'alarms':standard['ci95']['clean_alarms_per_1000']},'verdict':'NOT SUPPORTED' if 'NOT SUPPORTED' in safety else 'SUPPORTED' if all(x=='SUPPORTED' for x in safety) else 'INCONCLUSIVE'},
        {'id':'C4','claim':'Held-out-style damage ROC AUC >= 0.75','value':shift['auc'],'ci95':shift['ci95']['auc'],'verdict':verdict(shift['auc'],shift['ci95']['auc'],0.75)},
        {'id':'C5','claim':'Useful real-photograph discrimination demonstrated','value':None,'ci95':None,'verdict':'INCONCLUSIVE'}]
    results['operational']={s:[{'assumed_prevalence':rate,'false_reviews_per_1000':(1-rate)*results['models'][winner][s]['clean_alarms_per_1000'],
        'missed_damage_per_1000':rate*results['models'][winner][s]['damage_misses_per_1000'],
        'reviews_per_1000':(1-rate)*results['models'][winner][s]['clean_alarms_per_1000']+rate*results['models'][winner][s]['recall']*1000}
        for rate in [0.01,0.05,0.2]] for s in ['test','shift']}
    dump(DATA/'results.json',results)
    from .site_v2 import build
    build(ROOT,results)
    print('Completed: data/v2/results.json and docs/',flush=True)

def write_iterations(trials,winner):
    lines=['# Validation iteration log','', 'Predetermined candidates, training seed 20261029. Checkpoints and calibration use validation only. Test features are not extracted until this log and frozen.json have been written.','',
        '| Model | Change and reason | Validation F1 | AUC | Recall | Clean alarms / 1,000 | Epoch | Outcome |','| --- | --- | --- | --- | --- | --- | --- | --- |']
    reasons={'linear':'Learn weights over fixed pixel summaries','neural32':'Add nonlinear interactions','ablate_spatial':'Remove spatial layout to measure its contribution','ablate_normalization':'Remove intensity normalization to measure its contribution'}
    for r in trials:
        m=r['validation'];reason=next(v for k,v in reasons.items() if r['name'].startswith(k))
        outcome='KEPT: frozen final model' if r['name']==winner else 'ABLATION: diagnostic only' if r['purpose']=='ablation' else 'DROPPED: lower validation selection rank'
        lines.append(f"| {r['name']} | {reason} | {m['f1']:.4f} | {m['auc']:.4f} | {m['recall']:.4f} | {m['clean_alarms_per_1000']:.1f} | {r['best_epoch']} | {outcome} |")
    lines+=['','All six fits are retained, including negative ablations. Per-epoch validation log loss and elapsed CPU fit time are in data/v2/iterations.json. This is a bounded grid, not six sequential discoveries. No post-test model revision is allowed.']
    (ROOT/'ITERATIONS.md').write_text('\n'.join(lines)+'\n')

if __name__=='__main__':main()
