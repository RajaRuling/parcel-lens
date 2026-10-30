"""Export fixed detector results for a static, offline interactive viewer."""
import json
from pathlib import Path
import shutil
from PIL import Image, ImageDraw
from .evaluate import evaluate

ROOT=Path(__file__).resolve().parents[1]

def build():
    if (ROOT/'README.md').exists(): shutil.copyfile(ROOT/'README.md',ROOT/'docs/README.md')
    report=evaluate(ROOT/'data')
    (ROOT/'data/results.json').write_text(json.dumps(report,indent=2)+'\n')
    assets=ROOT/'docs/assets'; assets.mkdir(exist_ok=True)
    for record in report['records']:
        name=Path(record['file']).name
        shutil.copyfile(ROOT/'data'/record['file'],assets/name)
        record['image']='assets/'+name
    (assets/'demo-data.js').write_text('window.PARCEL_DATA = '+json.dumps(report,indent=2)+';\n')
    # A permanent inspection sheet separates predictions from labels by color.
    examples=[report['records'][i] for i in [0,1,2,3,4,19,20,23]]
    sheet=Image.new('RGB',(1280,4*480),(239,243,247)); d=ImageDraw.Draw(sheet)
    for i,record in enumerate(examples):
        x,y=(i%2)*640,(i//2)*480
        with Image.open(ROOT/'data'/record['file']) as image: sheet.paste(image,(x,y))
        for obj in record['predictions']:
            b=obj['box']; d.rectangle((b[0]+x,b[1]+y,b[2]+x,b[3]+y),outline='#bb3c21',width=3)
        for obj in record['objects']:
            b=obj['box']; left,top,right,bottom=b[0]+x,b[1]+y,b[2]+x,b[3]+y
            for xx in range(left,right,12):
                for yy in [top,bottom]: d.line((xx,yy,min(xx+6,right),yy),fill='#087f8c',width=3)
            for yy in range(top,bottom,12):
                for xx in [left,right]: d.line((xx,yy,xx,min(yy+6,bottom)),fill='#087f8c',width=3)
        label=record['objects'][0]['label'] if record['objects'] else 'intact'
        d.text((x+20,y+446),record['id']+' | '+label+' | predictions '+str(len(record['predictions'])),fill=(20,35,48))
        d.text((x+20,y+463),'Dashed teal: labels. Solid orange: predictions.',fill=(20,35,48))
    sheet.save(assets/'inspection-sheet.png')
    return report

if __name__=='__main__': build()
