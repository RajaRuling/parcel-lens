"""Scene-level binary metrics, tied-score ranking, and seeded uncertainty."""
import numpy as np

METRICS=['precision','recall','f1','auc','average_precision','brier','ece','clean_alarms_per_1000','damage_misses_per_1000']

def metrics(y,p,threshold=0.5):
    y=np.asarray(y,dtype=int);p=np.asarray(p,dtype=float)
    if len(y)!=len(p) or not len(y):raise ValueError('Nonempty aligned observations required')
    if not np.isin(y,[0,1]).all() or not np.isfinite(p).all() or (p<0).any() or (p>1).any():raise ValueError('Invalid labels or probabilities')
    pred=p>=threshold;tp=int(np.sum(pred&(y==1)));fp=int(np.sum(pred&(y==0)));fn=int(np.sum(~pred&(y==1)));tn=int(np.sum(~pred&(y==0)))
    ratio=lambda a,b:float(a/b) if b else None
    precision=ratio(tp,tp+fp);recall=ratio(tp,tp+fn)
    order=np.argsort(-p,kind='stable');ys=y[order];ps=p[order]
    ends=np.r_[np.flatnonzero(np.diff(ps)),len(ps)-1];ct=np.cumsum(ys)[ends];cf=ends+1-ct
    auc=ap=None
    if y.sum() and (1-y).sum():
        auc=float(np.trapezoid(np.r_[0,ct/y.sum()],np.r_[0,cf/(1-y).sum()]))
        ap=float(np.sum(np.diff(np.r_[0,ct])/y.sum()*ct/(ends+1)))
    ece=0.;bins=[]
    for j in range(10):
        take=(p>=j/10)&((p<(j+1)/10) if j<9 else p<=1)
        n=int(take.sum());mean=float(p[take].mean()) if n else None;freq=float(y[take].mean()) if n else None
        if n:ece+=n/len(y)*abs(mean-freq)
        bins.append({'low':j/10,'high':(j+1)/10,'n':n,'score':mean,'observed':freq})
    return {'n':len(y),'positives':int(y.sum()),'negatives':int((1-y).sum()),'threshold':float(threshold),
        'confusion':{'tn':tn,'fp':fp,'fn':fn,'tp':tp},'precision':precision,'recall':recall,'f1':ratio(2*tp,2*tp+fp+fn),
        'auc':auc,'average_precision':ap,'brier':float(np.mean((p-y)**2)),'ece':ece,'calibration':bins,
        'clean_alarms_per_1000':None if not tn+fp else 1000*fp/(tn+fp),
        'damage_misses_per_1000':None if not tp+fn else 1000*fn/(tp+fn),
        'zero_alarm_exact_upper_per_1000':1000*(1-0.05**(1/(tn+fp))) if fp==0 and tn+fp else None}

def sample_indices(y,rng):
    pools=[np.flatnonzero(np.asarray(y)==i) for i in [0,1]]
    return np.concatenate([rng.choice(pool,len(pool),replace=True) for pool in pools if len(pool)])

def with_ci(y,p,threshold=0.5,repeats=1000,seed=20261029):
    y=np.asarray(y);p=np.asarray(p);point=metrics(y,p,threshold);rng=np.random.default_rng(seed)
    values={key:[] for key in METRICS}
    for _ in range(repeats):
        idx=sample_indices(y,rng);m=metrics(y[idx],p[idx],threshold)
        for key in METRICS:
            if m[key] is not None:values[key].append(m[key])
    point['ci95']={key:list(map(float,np.percentile(v,[2.5,97.5]))) if v else None for key,v in values.items()}
    return point

def paired_difference(y,p,q,t,u,repeats=1000,seed=20261029):
    rng=np.random.default_rng(seed);y=np.asarray(y);p=np.asarray(p);q=np.asarray(q);values=[]
    for _ in range(repeats):
        idx=sample_indices(y,rng);values.append(metrics(y[idx],p[idx],t)['f1']-metrics(y[idx],q[idx],u)['f1'])
    return {'metric':'f1_difference','value':metrics(y,p,t)['f1']-metrics(y,q,u)['f1'],'ci95':list(map(float,np.percentile(values,[2.5,97.5])))}

def select_threshold(y,p):
    # Include an always-review and a never-review decision, even for tied scores.
    thresholds=np.unique(np.r_[0,p,1.000001]);rows=[metrics(y,p,t) for t in thresholds]
    eligible=[r for r in rows if r['recall'] is not None and r['recall']>=0.9]
    best=min(eligible,key=lambda r:(r['clean_alarms_per_1000'],-(r['f1'] or 0),-r['threshold'])) if eligible else max(rows,key=lambda r:(r['f1'] or 0,r['threshold']))
    return best

def verdict(value,ci,threshold,higher=True):
    if value is None or ci is None:return 'INCONCLUSIVE'
    if higher:
        if ci[0]>=threshold:return 'SUPPORTED'
        return 'NOT SUPPORTED' if value<threshold else 'INCONCLUSIVE'
    if ci[1]<=threshold:return 'SUPPORTED'
    return 'NOT SUPPORTED' if value>threshold else 'INCONCLUSIVE'
