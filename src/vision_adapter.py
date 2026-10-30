"""Optional OpenAI-compatible vision request. Never invoked by the demo or evaluation."""
import argparse
import base64
import json
import math
import os
from pathlib import Path
import urllib.request
from .generate import LABELS

PROMPT = ('Inspect this parcel for visible damage. Return only a JSON object with a detections array. '
          'Each detection has label and box. Labels: '+', '.join(LABELS)+'. '
          'box is [left, top, right, bottom] in 0 to 1000 image coordinates. '
          'Use tight boxes around damage, not the whole parcel. If uncertain return no detection. '
          'Return {"detections": []} for no visible damage.')

def validate_response(payload):
    if not isinstance(payload,dict) or not isinstance(payload.get('detections'),list):
        raise ValueError('Expected detections array')
    result=[]
    for item in payload['detections']:
        if not isinstance(item,dict) or item.get('label') not in LABELS: raise ValueError('Unknown label')
        box=item.get('box')
        if not isinstance(box,list) or len(box)!=4: raise ValueError('Expected 4 coordinates')
        if any(isinstance(x,bool) or not isinstance(x,(float,int)) or not math.isfinite(x) or not 0<=x<=1000 for x in box):
            raise ValueError('Coordinates must be finite numbers in 0 to 1000')
        if box[0]>=box[2] or box[1]>=box[3]: raise ValueError('Box must have positive area')
        result.append({'label':item['label'],'box':box})
    return result

def request_boxes(image):
    endpoint=os.environ.get('VISION_BASE_URL','').rstrip('/')
    model=os.environ.get('VISION_MODEL','')
    if not endpoint or not model: raise ValueError('Set VISION_BASE_URL and VISION_MODEL')
    if not endpoint.startswith(('https://','http://localhost:','http://127.0.0.1:')):
        raise ValueError('Use HTTPS or a loopback endpoint')
    from PIL import Image
    import io
    with Image.open(image) as source:
        source=source.convert('RGB'); source.thumbnail((1600,1600)); buf=io.BytesIO(); source.save(buf,format='JPEG')
    encoded=base64.b64encode(buf.getvalue()).decode('ascii')
    body={'model':model,'temperature':0,'messages':[{'role':'user','content':[
        {'type':'text','text':PROMPT},{'type':'image_url','image_url':{'url':'data:image/jpeg;base64,'+encoded}}]}]}
    headers={'Content-Type':'application/json'}
    key=os.environ.get('VISION_API_KEY','')
    if key: headers['Authorization']='Bearer '+key
    req=urllib.request.Request(endpoint+'/chat/completions',data=json.dumps(body).encode(),headers=headers,method='POST')
    with urllib.request.urlopen(req,timeout=120) as response: payload=json.load(response)
    content=payload['choices'][0]['message']['content']
    return validate_response(json.loads(content))

if __name__=='__main__':
    parser=argparse.ArgumentParser(description='Sends the selected image to your configured endpoint.')
    parser.add_argument('image',type=Path); args=parser.parse_args()
    try: print(json.dumps({'detections':request_boxes(args.image)},indent=2))
    except Exception:
        parser.exit(1,'Vision request failed. Check endpoint, model availability and response schema. No credentials logged.\n')
