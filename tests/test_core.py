import copy
import json
from pathlib import Path
import numpy as np
import pytest
from PIL import Image
from src.detector import detect
from src.evaluate import iou, match, evaluate
from src.generate import LABELS, scene, generate
from src.vision_adapter import validate_response, request_boxes
from src.check_public import scan, DENIED

ROOT=Path(__file__).resolve().parents[1]

@pytest.mark.parametrize('a,b,expected',[
    ([0,0,10,10],[0,0,10,10],1),([0,0,10,10],[10,0,20,10],0),
    ([0,0,10,10],[5,0,15,10],1/3),([0,0,0,0],[0,0,0,0],0),
    ([0,0,20,20],[5,5,15,15],.25)])
def test_iou(a,b,expected): assert iou(a,b)==pytest.approx(expected)

def test_duplicate_is_false_positive():
    obj={'label':LABELS[0],'box':[0,0,20,20]}
    assert match([obj],[obj,obj])[LABELS[0]]=={'tp':1,'fp':1,'fn':0}

def test_wrong_type_is_false_positive_and_miss():
    gt={'label':LABELS[0],'box':[0,0,20,20]}; pred={**gt,'label':LABELS[1]}
    rows=match([gt],[pred]);assert rows[LABELS[0]]['fn']==1;assert rows[LABELS[1]]['fp']==1

def test_exact_iou_threshold_is_inclusive():
    obj={'label':LABELS[0],'box':[0,0,10,10]}
    assert match([obj],[{**obj,'box':[0,0,20,10]}])[LABELS[0]]['tp']==1

@pytest.mark.parametrize('label',LABELS+[None])
def test_seeded_scene_repeatability(label):
    a,gt=scene(73,label);b,gt2=scene(73,label)
    assert a.tobytes()==b.tobytes() and gt==gt2
    if label:
        x0,y0,x1,y1=gt[0]['box'];assert 0<=x0<x1<=a.width and 0<=y0<y1<=a.height

@pytest.mark.parametrize('label',LABELS)
def test_detect_standard_development_scene(label):
    image,gt=scene(4100+LABELS.index(label),label)
    rows=match(gt,detect(image))
    assert rows[label]['tp']==1

def test_detector_reads_no_annotation_and_does_not_mutate():
    image,_=scene(4172,'water_stain');before=image.tobytes()
    assert detect(image)==detect(image.copy()) and image.tobytes()==before

@pytest.mark.parametrize('size',[(20,20),(640,440)])
def test_blank_image_has_no_detection(size): assert detect(Image.new('RGB',size,'white'))==[]

def test_manifest_has_disjoint_reproducible_splits():
    manifest=json.loads((ROOT/'data/annotations.json').read_text()); records=manifest['records']
    assert len(records)==40 and len({r['seed'] for r in records})==40
    assert sum(r['split']=='test' for r in records)==30
    for r in records:
        image,objects=scene(r['seed'],r['objects'][0]['label'] if r['objects'] else None,r['difficult'])
        assert objects==r['objects']
        with Image.open(ROOT/'data'/r['file']) as saved: assert image.tobytes()==saved.tobytes()

def test_cached_metrics_reproduce_with_no_network(monkeypatch):
    import urllib.request
    monkeypatch.setattr(urllib.request,'urlopen',lambda *a,**k:pytest.fail('Network forbidden'))
    measured=evaluate(ROOT/'data'); saved=json.loads((ROOT/'data/results.json').read_text())
    assert measured==saved
    assert measured['overall']['tp']+measured['overall']['fn']==25
    assert measured['clean_images']==5
    assert measured['overall']['fp']>0 and measured['overall']['fn']>0

@pytest.mark.parametrize('box',[[0,0,1000,1000],[20.5,80,300,600]])
def test_adapter_schema(box): assert validate_response({'detections':[{'label':LABELS[0],'box':box}]})[0]['box']==box

@pytest.mark.parametrize('box',[[0,0,1001,500],[0,0,0,1],[5,0,1,5],[False,0,2,3],[0,0,float('nan'),500],[0,0,1],[0,0,'a',4]])
def test_adapter_rejects_invalid_coordinates(box):
    with pytest.raises(ValueError): validate_response({'detections':[{'label':LABELS[0],'box':box}]})

@pytest.mark.parametrize('payload',[{},[],{'detections':[{'label':'unknown','box':[0,0,5,5]}]}])
def test_adapter_rejects_invalid_structure(payload):
    with pytest.raises(ValueError):validate_response(payload)

def test_adapter_requires_explicit_configuration(monkeypatch):
    monkeypatch.delenv('VISION_BASE_URL',raising=False);monkeypatch.delenv('VISION_MODEL',raising=False)
    with pytest.raises(ValueError):request_boxes(ROOT/'data/images/test_00.png')

def test_public_assets_contain_no_restricted_terms():assert scan()==[]

def test_public_scan_catches_mixed_case(tmp_path):
    (tmp_path/'example.txt').write_text(DENIED[0].upper())
    assert len(scan(tmp_path))==1

def test_demo_data_is_the_measured_report():
    content=(ROOT/'docs/assets/evidence.js').read_text()
    data=json.loads(content.removeprefix('window.PARCEL_V2 = ').removesuffix(';\n'))
    saved=json.loads((ROOT/'data/v2/results.json').read_text())
    assert data['claims']==saved['claims'] and data['models']==saved['models']
    assert len(data['test_records'])==1800
    for record in data['examples']:
        assert (ROOT/'docs'/record['image']).is_file()
        original=next(r for r in saved['test_records'] if r['id']==record['id'])
        assert record['score']==original['score'] and record['objects']==original['objects']
