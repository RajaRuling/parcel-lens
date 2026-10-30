"""Seeded procedural scenes, with annotations derived from drawn damage masks."""
import json
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

LABELS = ['dent_crush', 'tear_puncture', 'water_stain', 'open_flap', 'crushed_corner']
W, H = 640, 440

def scene(seed, label=None, difficult=False):
    rng = np.random.default_rng(seed)
    arr = np.full((H, W, 3), [226, 233, 237], dtype=float)
    arr += rng.normal(0, 1.4, (H, W, 1))
    image = Image.fromarray(np.uint8(np.clip(arr, 0, 255)))
    d = ImageDraw.Draw(image)
    x0, y0 = int(rng.integers(85, 110)), int(rng.integers(95, 120))
    x1, y1 = int(rng.integers(520, 550)), int(rng.integers(355, 385))
    base = np.array([187, 145, 94]) + rng.integers(-12, 13)
    d.rounded_rectangle((x0+7, y0+12, x1+13, y1+15), 8, fill=(195,203,207))
    d.rectangle((x0,y0,x1,y1), fill=tuple(base))
    for _ in range(900):
        x,y = int(rng.integers(x0,x1)), int(rng.integers(y0,y1))
        c = tuple(np.clip(base+rng.integers(-7,8),0,255))
        d.line((x,y,x+int(rng.integers(1,8)),y),fill=c)
    d.rectangle((x0+195,y0,x0+217,y1),fill=(207,175,124))
    d.line((x0+206,y0,x0+206,y1),fill=(170,133,88),width=2)
    d.rectangle((x0+25,y0+25,x0+120,y0+65),fill=(239,234,219))
    for j in range(8):
        d.line((x0+35+j*9,y0+32,x0+35+j*9,y0+57), fill=(110,108,99),width=2)
    mask = Image.new('L',(W,H)); m=ImageDraw.Draw(mask)
    cx, cy = int(rng.integers(x0+95,x1-95)), int(rng.integers(y0+95,y1-60))
    w,h=int(rng.integers(65,115)),int(rng.integers(40,68))
    color=(90,67,44)
    if label == 'dent_crush':
        pts=[(cx-w//2,cy),(cx-w//3,cy-h//2),(cx+w//2,cy-h//3),(cx+w//3,cy+h//2)]
        m.polygon(pts,fill=255); color=tuple(np.clip(base-[45,43,35],0,255))
    elif label == 'tear_puncture':
        pts=[(cx-w//2,cy-h//3),(cx-w//5,cy-h//2),(cx,cy-h//4),(cx+w//3,cy-h//2),(cx+w//2,cy),(cx+w//4,cy+h//2),(cx,cy+h//3),(cx-w//3,cy+h//2)]
        m.polygon(pts,fill=255); color=(45,37,29)
    elif label == 'water_stain':
        m.ellipse((cx-w//2,cy-h//2,cx+w//2,cy+h//2),fill=255)
        color=tuple(np.clip(base-[26,35,30],0,255))
        if difficult: color=tuple(np.clip(base-[10,12,10],0,255))
    elif label == 'open_flap':
        cx = (x0+x1)//2; cy=y0+8; w=int(rng.integers(100,170)); h=32
        m.polygon([(cx-w//2,cy),(cx,cy-24),(cx+w//2,cy),(cx+w//2,cy+14),(cx-w//2,cy+14)],fill=255)
        color=(64,48,32)
    elif label == 'crushed_corner':
        cx,cy=x1,y1; w,h=int(rng.integers(45,75)),int(rng.integers(38,65))
        m.polygon([(cx-w,cy),(cx,cy-h),(cx,cy)],fill=255); color=(99,74,49)
    image.paste(color, (0,0,W,H), mask)
    if label == 'dent_crush':
        d=ImageDraw.Draw(image)
        d.line((cx-w//3,cy,cx+w//3,cy+h//5),fill=(98,75,51),width=3)
    if difficult and label == 'tear_puncture':
        ImageDraw.Draw(image).rectangle((cx-8,cy-h,cx+8,cy+h),fill=(207,175,124))
    if difficult and label is None:
        ImageDraw.Draw(image).ellipse((x0+260,y0+130,x0+335,y0+180),fill=(47,38,30))
    image=image.filter(ImageFilter.GaussianBlur(0.45 if not difficult else 0.9))
    bbox=mask.getbbox()
    return image, ([] if label is None else [{'label':label,'box':list(bbox)}])

def generate(root):
    root=Path(root); (root/'images').mkdir(parents=True,exist_ok=True)
    records=[]
    for split,count,start in [('development',10,4100),('test',30,92000)]:
        for i in range(count):
            label=LABELS[i%6] if i%6<5 else None
            difficult=split=='test' and i>=18
            image,objects=scene(start+i,label,difficult)
            name=f'{split}_{i:02}.png'; image.save(root/'images'/name)
            records.append({'id':name[:-4],'file':'images/'+name,'split':split,'seed':start+i,
                            'synthetic':True,'difficult':difficult,'objects':objects})
    manifest={'schema':'xyxy pixel bounds, exclusive right and bottom','size':[W,H],
              'generator':'procedural illustration v1','records':records}
    (root/'annotations.json').write_text(json.dumps(manifest,indent=2)+'\n')
    return manifest

if __name__=='__main__':
    generate(Path(__file__).resolve().parents[1]/'data')
