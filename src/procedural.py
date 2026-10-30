"""Independent scene rendering and preassigned source-level splits, version 2."""
import hashlib
import json
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from .generate import LABELS

W,H=224,168
SPLITS={'train':(2400,120000),'validation':(600,220000),'test':(900,320000),'shift':(900,420000)}

def specifications():
    records=[]
    for split,(count,start) in SPLITS.items():
        rng=np.random.default_rng(start)
        labels=np.tile(np.array(['clean']*5+LABELS),count//10)
        rng.shuffle(labels)
        # Nuisance labels depend on the scene index, never on the damage class.
        for i,label in enumerate(labels):
            records.append({'id':f'{split}_{i:04d}','split':split,'seed':start+i,
                'label':str(label),'damaged':int(label!='clean'),
                'severity':['mild','moderate','severe'][(i//3)%3] if label!='clean' else 'none',
                'lighting':['dim','neutral','bright'][i%3],
                'style':'shift' if split=='shift' else 'standard','synthetic':True})
    return records

def render(record):
    rng=np.random.default_rng(record['seed']); shifted=record['style']=='shift'
    base=np.array([177,137,91])+rng.normal(0,12,3)
    bg=rng.uniform(110,230,3) if not shifted else rng.uniform(35,160,3)
    yy,xx=np.mgrid[:H,:W]
    pixels=np.tile(bg,(H,W,1))+rng.normal(0,3,(H,W,1))
    pixels+=((xx/W+yy/H)*rng.uniform(-15,15))[...,None]
    image=Image.fromarray(np.uint8(np.clip(pixels,0,255)));d=ImageDraw.Draw(image)
    x0=int(rng.integers(24,48));y0=int(rng.integers(28,48))
    x1=int(rng.integers(175,204));y1=int(rng.integers(126,151));depth=int(rng.integers(8,19))
    color=lambda v:tuple(np.uint8(np.clip(v,0,255)))
    d.rectangle((x0+6,y0+12,x1+9,y1+9),fill=color(bg-30))
    d.polygon([(x0,y0),(x0+depth,y0-depth),(x1,y0-depth),(x1,y0)],fill=color(base+20))
    d.rectangle((x0,y0,x1,y1),fill=color(base))
    d.polygon([(x1-depth,y0),(x1,y0-depth),(x1,y1),(x1-depth,y1-5)],fill=color(base-22))
    for _ in range(240):
        x=int(rng.integers(x0,x1));y=int(rng.integers(y0,y1))
        d.line((x,y,min(x1,x+int(rng.integers(1,8))),y),fill=color(base+rng.normal(0,6)),width=1)
    # Tape and printing occur in every class with the same distribution.
    tape_x=int(rng.integers(x0+10,x1-20)); tape_w=int(rng.integers(5,14))
    d.rectangle((tape_x,y0,tape_x+tape_w,y1),fill=color(base+[24,23,20]))
    d.line((tape_x+tape_w//2,y0,tape_x+tape_w//2,y1),fill=color(base-10))
    lx=int(rng.integers(x0+4,x1-42));ly=int(rng.integers(y0+3,y1-25))
    d.rectangle((lx,ly,lx+35,ly+22),fill=(229,228,218))
    for k in range(10):
        d.line((lx+3+k*3,ly+5,lx+3+k*3,ly+16),fill=(65,65,60),width=int(rng.integers(1,3)))
    for _ in range(int(rng.integers(0,4))):
        cx=int(rng.integers(x0+5,x1-8));cy=int(rng.integers(y0+5,y1-8))
        d.line((cx,cy,cx+int(rng.integers(3,14)),cy+int(rng.integers(-4,5))),fill=color(base-rng.uniform(15,55)),width=1)
    mask=Image.new('L',(W,H));m=ImageDraw.Draw(mask)
    label=record['label'];severity=record['severity'];strength={'none':0,'mild':0.4,'moderate':0.7,'severe':1}[severity]
    cx=int(rng.integers(x0+18,x1-22));cy=int(rng.integers(y0+15,y1-15))
    rw=int(12+22*strength);rh=int(7+13*strength)
    damage_color=base-(20+50*strength)
    if label=='dent_crush':
        m.polygon([(cx-rw,cy),(cx-rw//2,cy-rh),(cx+rw,cy-rh//2),(cx+rw//2,cy+rh)],fill=255)
    elif label=='tear_puncture':
        m.polygon([(cx-rw,cy-rh//2),(cx-3,cy-rh),(cx+3,cy-2),(cx+rw,cy-rh//2),(cx+rw//2,cy+rh),(cx-3,cy+rh//2)],fill=255)
        damage_color=base*(0.75-0.5*strength)
    elif label=='water_stain':
        m.ellipse((cx-rw,cy-rh,cx+rw,cy+rh),fill=255)
        mask=mask.filter(ImageFilter.GaussianBlur(2));damage_color=base-[12+18*strength,14+24*strength,8+15*strength]
    elif label=='open_flap':
        cy=y0; m.polygon([(cx-rw,cy+3),(cx,cy-int(5+12*strength)),(cx+rw,cy+2),(cx+rw,cy+7),(cx-rw,cy+7)],fill=255)
        damage_color=base*(0.6-0.3*strength)
    elif label=='crushed_corner':
        cx=x1;cy=y1;m.polygon([(cx-rw,cy),(cx,cy-rh*2),(cx,cy)],fill=255)
    if label!='clean': image.paste(color(damage_color),(0,0,W,H),mask)
    d=ImageDraw.Draw(image)
    if label=='dent_crush':d.line((cx-rw//2,cy,cx+rw//2,cy+rh//2),fill=color(base-80*strength),width=1)
    # Tape can obscure actual damage; it is not removed from ground truth.
    occluded=bool(rng.random()<0.2)
    if occluded:
        ox=int(rng.integers(x0+10,x1-10));d.rectangle((ox,y0,ox+9,y1),fill=color(base+15))
    angle=float(rng.uniform(-8,8) if not shifted else rng.choice([-1,1])*rng.uniform(16,28))
    image=image.rotate(angle,resample=Image.Resampling.BICUBIC,fillcolor=color(bg))
    mask=mask.rotate(angle,resample=Image.Resampling.NEAREST)
    if shifted:
        d=ImageDraw.Draw(image)
        for _ in range(5):
            a=int(rng.integers(0,W));b=int(rng.integers(0,H));d.rectangle((a,b,min(W-1,a+12),min(H-1,b+8)),fill=color(bg+rng.uniform(-20,20)))
    pixels=np.asarray(image,dtype=float)
    gain={'dim':0.62,'neutral':1,'bright':1.22}[record['lighting']]
    gradient=1+rng.uniform(-0.35,0.35)*(xx/W-0.5)
    pixels*=gain*gradient[...,None]
    if shifted:pixels*=np.array([0.84,1.02,1.16])
    pixels+=rng.normal(0,6 if shifted else rng.uniform(0.5,3),(H,W,1))
    image=Image.fromarray(np.uint8(np.clip(pixels,0,255))).filter(ImageFilter.GaussianBlur(float(rng.uniform(0,0.8 if shifted else 0.4))))
    bbox=mask.getbbox()
    return image,([] if bbox is None else [{'label':label,'box':list(bbox)}]),occluded

def generate(root):
    root=Path(root);folder=root/'images';folder.mkdir(parents=True,exist_ok=True)
    records=specifications()
    # Persist split identities before any images or features are produced.
    (root/'split-plan.json').write_text(json.dumps(records,indent=2)+'\n')
    for r in records:
        image,objects,occluded=render(r);r['objects']=objects;r['tape_occlusion']=occluded
        r['file']='images/'+r['id']+'.png';image.save(root/r['file'])
        r['sha256']=hashlib.sha256((root/r['file']).read_bytes()).hexdigest()
    (root/'annotations.json').write_text(json.dumps({'version':2,'size':[W,H],'records':records},indent=2)+'\n')
    return records
