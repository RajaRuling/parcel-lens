"""Check saved evidence integrity without fitting or querying any remote service."""
import hashlib
import json
from pathlib import Path
import numpy as np
from PIL import Image
from .learned import Head
from .predict import predict
from .statistics import metrics

ROOT=Path(__file__).resolve().parents[1]

def main():
    folder=ROOT/'data/v2';data=json.loads((folder/'results.json').read_text());frozen=json.loads((folder/'frozen.json').read_text())
    rows=json.loads((folder/'annotations.json').read_text())['records']
    assert len(rows)==4800 and len({r['id'] for r in rows})==4800 and len({r['seed'] for r in rows})==4800
    assert len({r['sha256'] for r in rows})==4800
    for r in rows:assert hashlib.sha256((folder/r['file']).read_bytes()).hexdigest()==r['sha256'],r['id']
    assert hashlib.sha256((ROOT/'EXPERIMENTS.md').read_bytes()).hexdigest()==frozen['plan_sha256']
    for name,digest in frozen['model_sha256'].items():assert hashlib.sha256((folder/'models'/name).read_bytes()).hexdigest()==digest,name
    for split in ['test','shift']:
        part=[r for r in data['test_records'] if r['split']==split];assert len(part)==900
        point=metrics([r['damaged'] for r in part],[r['score'] for r in part],frozen['thresholds'][frozen['winner']])
        saved=data['models'][frozen['winner']][split]
        for key,value in point.items():assert value==saved[key],(split,key)
    js=(ROOT/'docs/assets/evidence.js').read_text()
    site=json.loads(js.removeprefix('window.PARCEL_V2 = ').removesuffix(';\n'))
    for key in data:assert site[key]==data[key],key
    assert json.loads((ROOT/'docs/assets/results.json').read_text())==data
    model=Head.load(folder/'models'/(frozen['winner']+'.npz'))
    for row in site['examples']:
        assert (ROOT/'docs'/row['image']).read_bytes()==(folder/row['file']).read_bytes()
        # Test persisted inference on displayed examples, without changing the model or threshold.
        with Image.open(folder/row['file']) as image:pred=predict(image,model,frozen['thresholds'][frozen['winner']])
        assert np.isclose(pred['synthetic_validation_score'],row['score'],atol=1e-12,rtol=0),row['id']
        assert pred['production_auto_clear'] is False
    first=folder/'first-evaluation.json';reproduction=None
    if first.exists():
        original=json.loads(first.read_text())
        for key in ['models','paired','claims','operational','threshold_curves','test_records','subgroups']:
            assert original[key]==data[key],f'reproduction differs: {key}'
        for key in ['winner','thresholds','plan_sha256']:assert original['frozen'][key]==frozen[key]
        reproduction='identical scores, point metrics, intervals, claims, thresholds and records'
    report={'source_images_hash_verified':len(rows),'unique_source_seeds':4800,'unique_image_hashes':4800,
        'model_hashes_verified':len(frozen['model_sha256']),'site_json_matches_measured_results':True,
        'gallery_images_and_loaded_model_scores_verified':len(site['examples']),
        'point_metrics_recomputed_from_frozen_scores':True,'reproduction':reproduction,
        'no_model_refit':True,'external_requests':0}
    (folder/'verification.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))

if __name__=='__main__':main()
