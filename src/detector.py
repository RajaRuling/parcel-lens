"""Handwritten color and geometry baseline. Reads pixels only, never annotations."""
import argparse
import json
from collections import deque
from pathlib import Path
import numpy as np
from PIL import Image, ImageFilter

VERSION='color-geometry-v1'

def components(mask):
    seen=np.zeros(mask.shape,dtype=bool)
    for y,x in zip(*np.where(mask)):
        if seen[y,x]: continue
        todo=deque([(y,x)]); seen[y,x]=True; pixels=[]
        while todo:
            yy,xx=todo.popleft(); pixels.append((yy,xx))
            for ny,nx in [(yy-1,xx),(yy+1,xx),(yy,xx-1),(yy,xx+1)]:
                if 0<=ny<mask.shape[0] and 0<=nx<mask.shape[1] and mask[ny,nx] and not seen[ny,nx]:
                    seen[ny,nx]=True; todo.append((ny,nx))
        if len(pixels)>=28: yield np.array(pixels)

def detect(image):
    image=image.convert('RGB')
    width,height=image.size
    # Scale-independent processing; minimum useful input is 80 pixels wide.
    if width<80 or height<80: return []
    scale=320/width; small=image.resize((320,max(1,round(height*scale))))
    a=np.asarray(small).astype(float)
    r,g,b=a[:,:,0],a[:,:,1],a[:,:,2]
    cardboard=(r-g>22)&(g-b>23)&(r>130)
    yy,xx=np.where(cardboard)
    if len(xx)<500: return []
    left,right,top,bottom=int(xx.min()),int(xx.max()),int(yy.min()),int(yy.max())
    base=np.median(a[cardboard],axis=0)
    roi=np.zeros(cardboard.shape,dtype=bool)
    roi[max(0,top-16):bottom+1,left:right+1]=True
    # Dark marks on tan material. Closing connects creases and irregular holes.
    dark=(r<base[0]-18)&(g<base[1]-19)&(b<base[2]-12)&roi
    mask=np.asarray(Image.fromarray(dark.astype('uint8')*255).filter(ImageFilter.MaxFilter(5)).filter(ImageFilter.MinFilter(5)))>0
    out=[]
    for pixels in components(mask):
        ys,xs=pixels[:,0],pixels[:,1]
        x0,x1,y0,y1=int(xs.min()),int(xs.max()+1),int(ys.min()),int(ys.max()+1)
        bw,bh=x1-x0,y1-y0
        if bw<10 or bh<7: continue
        mean=np.median(a[ys,xs],axis=0)
        if y0<top+9 and bw>35: label='open_flap'
        elif x1>right-5 and y1>bottom-5: label='crushed_corner'
        elif mean[0]<85: label='tear_puncture'
        elif (base[1]-mean[1])-(base[0]-mean[0])>4: label='water_stain'
        else: label='dent_crush'
        out.append({'label':label,'box':[round(x0/scale),round(y0/scale),min(width,round(x1/scale)),min(height,round(y1/scale))],
                    'score':0.65})
    return out

if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('image',type=Path); args=p.parse_args()
    with Image.open(args.image) as image: print(json.dumps(detect(image),indent=2))
