"""Class-aware, one-to-one greedy matching at a fixed intersection-over-union."""
import json
from pathlib import Path
from PIL import Image
from .detector import detect, VERSION
from .generate import LABELS

def iou(a,b):
    inter=max(0,min(a[2],b[2])-max(a[0],b[0]))*max(0,min(a[3],b[3])-max(a[1],b[1]))
    union=max(0,a[2]-a[0])*max(0,a[3]-a[1])+max(0,b[2]-b[0])*max(0,b[3]-b[1])-inter
    return inter/union if union else 0.0

def match(truth,predictions,threshold=0.5):
    used=set(); result={label:{'tp':0,'fp':0,'fn':0} for label in LABELS}
    for pred in sorted(predictions,key=lambda p:p.get('score',0),reverse=True):
        candidates=[(iou(pred['box'],gt['box']),i) for i,gt in enumerate(truth) if i not in used and gt['label']==pred['label']]
        overlap,index=max(candidates,default=(0,-1))
        if index>=0 and overlap>=threshold: used.add(index); result[pred['label']]['tp']+=1
        else: result[pred['label']]['fp']+=1
    for i,gt in enumerate(truth):
        if i not in used: result[gt['label']]['fn']+=1
    return result

def rates(row):
    tp,fp,fn=row['tp'],row['fp'],row['fn']
    return {**row,'precision':tp/(tp+fp) if tp+fp else None,'recall':tp/(tp+fn) if tp+fn else None}

def evaluate(root,split='test'):
    root=Path(root); manifest=json.loads((root/'annotations.json').read_text())
    counts={l:{'tp':0,'fp':0,'fn':0} for l in LABELS}; predictions=[]; clean=clean_flagged=0
    for record in manifest['records']:
        if record['split']!=split: continue
        with Image.open(root/record['file']) as image: pred=detect(image)
        per=match(record['objects'],pred)
        for label,row in per.items():
            for k,v in row.items(): counts[label][k]+=v
        if not record['objects']: clean+=1; clean_flagged+=bool(pred)
        predictions.append({**record,'predictions':pred})
    total={k:sum(row[k] for row in counts.values()) for k in ['tp','fp','fn']}
    return {'detector':VERSION,'split':split,'synthetic':True,'iou_threshold':0.5,
            'images':len(predictions),'clean_images':clean,'clean_images_flagged':clean_flagged,
            'overall':rates(total),'per_type':{l:rates(r) for l,r in counts.items()},'records':predictions}

if __name__=='__main__':
    root=Path(__file__).resolve().parents[1]
    report=evaluate(root/'data'); (root/'data/results.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='records'},indent=2))
