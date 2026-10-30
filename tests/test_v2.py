"""Tiny offline checks for scene isolation, training, metrics and decisions."""
import numpy as np
import pytest
from src.procedural import specifications,render
from src.learned import features,Head
from src.statistics import metrics,with_ci,paired_difference,select_threshold,verdict


def test_splits_preassigned_and_disjoint():
    rows=specifications();assert len(rows)==4800
    assert len({r['seed'] for r in rows})==4800
    assert len({r['id'] for r in rows})==4800
    for split,n in [('train',2400),('validation',600),('test',900),('shift',900)]:
        part=[r for r in rows if r['split']==split];assert len(part)==n
        assert sum(r['damaged'] for r in part)==n//2
        for label in ['dent_crush','tear_puncture','water_stain','open_flap','crushed_corner']:
            assert sum(r['label']==label for r in part)==n//10
    assert {r['style'] for r in rows if r['split']=='train'}=={'standard'}
    assert {r['style'] for r in rows if r['split']=='shift'}=={'shift'}


def test_render_deterministic_and_annotated():
    r=next(r for r in specifications() if r['damaged'])
    a,boxes,o=render(r);b,other,oo=render(r)
    assert a.tobytes()==b.tobytes() and boxes==other and o==oo
    assert len(boxes)==1
    x0,y0,x1,y1=boxes[0]['box'];assert 0<=x0<x1<=224 and 0<=y0<y1<=168
    clean=next(r for r in specifications() if not r['damaged']);assert render(clean)[1]==[]
    f=features(a);assert len(f)==732 and np.isfinite(f).all()
    assert len(features(a,spatial=False))==12


@pytest.mark.parametrize('y,p,auc,ap',[
    ([0,0,1,1],[0.1,0.2,0.8,0.9],1,1),
    ([0,0,1,1],[0.5,0.5,0.5,0.5],0.5,0.5),
    ([0,0,1,1],[0.9,0.8,0.2,0.1],0,5/12),
])
def test_ranking_with_ties(y,p,auc,ap):
    m=metrics(y,p);assert m['auc']==pytest.approx(auc);assert m['average_precision']==pytest.approx(ap)


def test_bootstrap_and_paired_identity():
    y=np.array([0,0,1,1]);p=np.array([0.1,0.9,0.2,0.8])
    a=with_ci(y,p,repeats=30);b=with_ci(y,p,repeats=30);assert a==b
    assert paired_difference(y,p,p,0.5,0.5,repeats=20)['ci95']==[0,0]
    assert metrics([1,1],[0.3,0.8])['auc'] is None
    assert metrics([0,0],[0.1,0.2])['zero_alarm_exact_upper_per_1000']>0
    assert metrics([0,0],[0.1,0.2])['precision'] is None


def test_validation_threshold_and_verdicts():
    m=select_threshold([0,0,1,1],np.array([0.1,0.4,0.5,0.9]));assert m['threshold']==0.5 and m['recall']==1
    assert verdict(0.8,[0.7,0.9],0.8)=='INCONCLUSIVE'
    assert verdict(0.7,[0.6,0.8],0.8)=='NOT SUPPORTED'
    assert verdict(0.9,[0.8,1],0.8)=='SUPPORTED'
    assert verdict(200,[100,300],100,False)=='NOT SUPPORTED'


@pytest.mark.parametrize('hidden',[0,32])
def test_train_learns_and_reloads_without_network(tmp_path,hidden,monkeypatch):
    import urllib.request
    monkeypatch.setattr(urllib.request,'urlopen',lambda *a,**k:pytest.fail('Offline test'))
    rng=np.random.default_rng(42);x=rng.normal(size=(80,5));y=(x[:,0]+x[:,1]>0).astype(int)
    model=Head(hidden).fit(x[:60],y[:60],x[60:],y[60:],epochs=160)
    assert metrics(y[:60],model.predict(x[:60]))['auc']>0.8
    np.testing.assert_allclose(model.mean,x[:60].mean(axis=0))
    model.save(tmp_path/'model.npz');other=Head.load(tmp_path/'model.npz')
    model.fit_seconds=12345.
    model.save(tmp_path/'same-parameters.npz')
    assert (tmp_path/'model.npz').read_bytes()==(tmp_path/'same-parameters.npz').read_bytes()
    np.testing.assert_array_equal(model.predict(x),other.predict(x))
