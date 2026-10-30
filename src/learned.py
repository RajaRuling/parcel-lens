"""Trainable linear and neural image heads over fixed pixel summaries. CPU only."""
import time
import numpy as np
from PIL import Image,ImageFilter

SEED=20261029

def features(image,normalize=True,spatial=True):
    image=image.convert('RGB').resize((64,48))
    a=np.asarray(image,dtype=np.float64)/255
    if normalize:a=np.clip((a-a.mean())/(a.std()+0.05),-3,3)
    gray=a.mean(axis=2);dx=np.abs(np.diff(gray,axis=1,append=gray[:,-1:]));dy=np.abs(np.diff(gray,axis=0,append=gray[-1:,:]))
    blur=np.asarray(image.filter(ImageFilter.GaussianBlur(2)),dtype=float).mean(axis=2)/255
    original=np.asarray(image,dtype=float).mean(axis=2)/255
    residual=original-blur
    channels=np.concatenate([a,dx[...,None],dy[...,None],residual[...,None]],axis=2)
    out=[]
    for rows,cols in ([(1,1),(3,4),(6,8)] if spatial else [(1,1)]):
        for y in np.array_split(np.arange(48),rows):
            for x in np.array_split(np.arange(64),cols):
                part=channels[y[:,None],x]
                out.extend(part.mean(axis=(0,1)));out.extend(part.std(axis=(0,1)))
    return np.asarray(out,dtype=np.float64)

def sigmoid(z):return 1/(1+np.exp(-np.clip(z,-35,35)))
def logloss(y,p):
    p=np.clip(p,1e-9,1-1e-9);return float(-np.mean(y*np.log(p)+(1-y)*np.log(1-p)))

class Head:
    def __init__(self,hidden=0,regularization=0.001):self.hidden=hidden;self.regularization=regularization;self.temperature=1.
    def raw(self,x):
        x=np.clip((x-self.mean)/self.scale,-8,8)
        if self.hidden:return np.tanh(x@self.w1+self.b1)@self.w2+self.b2
        return x@self.w1+self.b1
    def predict(self,x):return sigmoid(self.raw(x)/self.temperature)
    def fit(self,x,y,xv,yv,epochs=160):
        start=time.monotonic();rng=np.random.default_rng(SEED)
        self.mean=x.mean(axis=0);self.scale=np.maximum(x.std(axis=0),0.02)
        z=np.clip((x-self.mean)/self.scale,-8,8);d=z.shape[1]
        self.w1=rng.normal(0,1/np.sqrt(d),(d,self.hidden)) if self.hidden else np.zeros(d)
        self.b1=np.zeros(self.hidden) if self.hidden else np.zeros(1)
        if self.hidden:self.w2=rng.normal(0,0.1,self.hidden);self.b2=np.zeros(1)
        names=['w1','b1']+(['w2','b2'] if self.hidden else [])
        m={k:np.zeros_like(getattr(self,k)) for k in names};v={k:np.zeros_like(getattr(self,k)) for k in names}
        best=float('inf');best_weights=None;step=0;self.history=[]
        for epoch in range(epochs):
            for batch in np.array_split(rng.permutation(len(z)),max(1,len(z)//128)):
                xb=z[batch];yb=y[batch];step+=1
                if self.hidden:
                    h=np.tanh(xb@self.w1+self.b1);err=(sigmoid(h@self.w2+self.b2)-yb)/len(batch)
                    dh=err[:,None]*self.w2*(1-h*h)
                    grads={'w2':h.T@err+self.regularization*self.w2,'b2':np.array([err.sum()]),'w1':xb.T@dh+self.regularization*self.w1,'b1':dh.sum(axis=0)}
                else:
                    err=(sigmoid(xb@self.w1+self.b1)-yb)/len(batch)
                    grads={'w1':xb.T@err+self.regularization*self.w1,'b1':np.array([err.sum()])}
                for k,g in grads.items():
                    m[k]=0.9*m[k]+0.1*g;v[k]=0.999*v[k]+0.001*g*g
                    setattr(self,k,getattr(self,k)-0.002*(m[k]/(1-0.9**step))/(np.sqrt(v[k]/(1-0.999**step))+1e-8))
            loss=logloss(yv,self.predict(xv));self.history.append(loss)
            if loss<best:
                best=loss;best_weights={k:getattr(self,k).copy() for k in names};self.best_epoch=epoch+1
            if time.monotonic()-start>19*60:break
        for k,value in best_weights.items():setattr(self,k,value)
        self.fit_seconds=round(time.monotonic()-start,3)
        temperatures=[0.5,0.75,1,1.5,2,3]
        raw=self.raw(xv);self.temperature=min(temperatures,key=lambda t:logloss(yv,sigmoid(raw/t)))
        return self
    def save(self,path):
        keys=['hidden','regularization','temperature','mean','scale','w1','b1']+(['w2','b2'] if self.hidden else [])
        values={key:getattr(self,key) for key in keys}
        np.savez(path,**values)
    @classmethod
    def load(cls,path):
        saved=np.load(path,allow_pickle=False);obj=cls()
        for key in saved.files:
            value=saved[key];setattr(obj,key,value.item() if value.ndim==0 else value)
        return obj
