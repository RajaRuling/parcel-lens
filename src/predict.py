"""Local inference for the frozen binary image classifier; no remote calls."""
import argparse
import json
from pathlib import Path
from PIL import Image
from .learned import Head,features

ROOT=Path(__file__).resolve().parents[1]

def predict(image,head,threshold):
    score=float(head.predict(features(image)[None,:])[0])
    return {'synthetic_validation_score':score,'review_threshold':threshold,
        'simulated_action':'review' if score>=threshold else 'clear',
        'production_auto_clear':False,'localization':'not predicted','real_image_accuracy':'untested'}

def main():
    parser=argparse.ArgumentParser();parser.add_argument('image',type=Path);args=parser.parse_args()
    frozen=json.loads((ROOT/'data/v2/frozen.json').read_text());winner=frozen['winner']
    model=Head.load(ROOT/'data/v2/models'/(winner+'.npz'))
    with Image.open(args.image) as image:result=predict(image,model,frozen['thresholds'][winner])
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()
