"""Build an offline static evidence site and written report from measured JSON."""
import json
import shutil
from pathlib import Path
from PIL import Image,ImageDraw


def number(value):return 'not measured' if value is None else f'{value:.4f}'
def interval(value,ci):return number(value)+(f' [{ci[0]:.4f}, {ci[1]:.4f}]' if ci else '')

def build(root,data):
    docs=root/'docs';assets=docs/'assets';assets.mkdir(exist_ok=True)
    # Retire version 1 gallery assets; the underlying legacy fixtures remain intact.
    for path in assets.glob('test_*.png'):path.unlink()
    for name in ['demo-data.js','inspection-sheet.png']:
        path=assets/name
        if path.exists():path.unlink()
    examples=[]
    for split in ['test','shift']:
        rows=[r for r in data['test_records'] if r['split']==split];chosen=[]
        def add(items,count):
            for row in items:
                if row['id'] not in {r['id'] for r in chosen}:chosen.append(row)
                if count<=1:break
                count-=1
        # Select failures for error analysis, not to estimate performance.
        add(sorted([r for r in rows if not r['damaged'] and r['review']],key=lambda r:-r['score']),4)
        add(sorted([r for r in rows if r['damaged'] and not r['review']],key=lambda r:r['score']),4)
        for label in ['clean','dent_crush','tear_puncture','water_stain','open_flap','crushed_corner']:
            add([r for r in rows if r['label']==label],2)
        for row in chosen:
            row=dict(row);row['image']='assets/'+row['id']+'.png'
            shutil.copyfile(root/'data/v2'/row['file'],docs/row['image']);examples.append(row)
    payload=dict(data);payload['examples']=examples
    (assets/'evidence.js').write_text('window.PARCEL_V2 = '+json.dumps(payload,allow_nan=False)+';\n')
    shutil.copyfile(root/'data/v2/results.json',assets/'results.json')
    # A durable visual contact sheet of the selected failures and controls.
    sheet=Image.new('RGB',(896,210*((len(examples)+3)//4)),(240,242,244));draw=ImageDraw.Draw(sheet)
    for i,row in enumerate(examples):
        x=(i%4)*224;y=(i//4)*210
        with Image.open(docs/row['image']) as image:sheet.paste(image,(x,y))
        text=f"{row['id']}  p={row['score']:.2f}\n{row['label']} / {'review' if row['review'] else 'clear'}"
        draw.text((x+5,y+171),text,fill=(20,25,30))
    sheet.save(assets/'error-contact-sheet.png')
    write_report(root,data)
    research=docs/'research';research.mkdir(exist_ok=True)
    for name in ['EXPERIMENTS.md','ITERATIONS.md','DATA.md','REPORT.md']:
        shutil.copyfile(root/name,research/name)


def write_report(root,data):
    winner=data['frozen']['winner'];threshold=data['frozen']['thresholds'][winner]
    lines=['# Parcel Lens — version 2 evidence report','',
        '**Result scope: 4,800 original procedural scenes; zero real photographs. Real-world accuracy is untested.**','',
        f"Frozen model: {winner}; review threshold {threshold:.6f}. Learned binary image classification; no learned bounding-box, damage-type or severity performance is claimed.",'',
        '## Registered claims','', '| ID | Claim | Estimate [95% CI] | Verdict |','| --- | --- | --- | --- |']
    for c in data['claims']:
        val=json.dumps(c['value']) if isinstance(c['value'],dict) else number(c['value']);ci=json.dumps(c['ci95']) if c['ci95'] else 'not available'
        lines.append(f"| {c['id']} | {c['claim']} | {val}; {ci} | {c['verdict']} |")
    lines+=['','## Frozen model comparison','',
        'Each candidate is evaluated once in the final pass. All thresholds and checkpoints were selected on validation only. Intervals below use 1,000 stratified scene-bootstrap resamples, fixed seed 20261029; prevalence is fixed at 50% within these resamples. C2 uses paired scene resamples. Undefined quantities are not measured. Bootstrap intervals are conditional on this generator and fitted model, not on alternate training sets or real networks.','']
    for split in ['test','shift']:
        lines +=[f'### {split}: 900 images, 450 clean / 450 damaged','',
            '| Model | Precision | Recall | F1 | AUC | Average precision | Brier | ECE | Clean alarms / 1,000 |','| --- | --- | --- | --- | --- | --- | --- | --- | --- |']
        for name,parts in data['models'].items():
            m=parts[split];values=[interval(m[k],m['ci95'][k]) for k in ['precision','recall','f1','auc','average_precision','brier','ece','clean_alarms_per_1000']]
            lines.append('| '+name+' | '+' | '.join(values)+' |')
        lines+=['','Confusion matrices are image-level: TN, FP, FN, TP.','']
        for name,parts in data['models'].items():lines.append(f"- {name}: {json.dumps(parts[split]['confusion'])}")
        delta=data['paired'][split];lines+=['',f"Selected model minus classical F1: {interval(delta['value'],delta['ci95'])}.",'']
    lines+=['## Subgroup results','',
        'Type and severity subsets consist of damaged images only; the meaningful decision metric is recall. Clean rows contain only negatives; alarm rate is meaningful there. Lighting and tape subsets include both classes. All subgroup metrics and CIs, including undefined fields, are in the JSON. No adjustment for multiple comparisons; use these slices to find weaknesses, not to rank universal damage difficulty.','']
    for split,fields in data['subgroups'].items():
        lines +=[f'### {split}','', '| Slice | Value | N | Recall [95% CI] | Clean alarms / 1,000 [95% CI] |','| --- | --- | --- | --- | --- |']
        for field,values in fields.items():
            for value,m in values.items():lines.append(f"| {field} | {value} | {m['n']} | {interval(m['recall'],m['ci95']['recall'])} | {interval(m['clean_alarms_per_1000'],m['ci95']['clean_alarms_per_1000'])} |")
    lines+=['','## Review decision and sensitivity','',
        'At or above the frozen threshold: flag the image for a person to inspect. Below it: the simulated policy clears the image. **Production auto-clear remains disabled:** this study does not validate real-image safety, content condition, claims liability or multi-parcel inspection. A reviewer needs the original image, image score, capture context, views of other sides and the physical parcel when ambiguous. Do not infer damage absence from a hidden face. Ground-truth overlays in the gallery are generator annotations, not predictions.','']
    for split in ['test','shift']:
        m=data['models'][winner][split]
        lines+=[f"On {split}: {interval(m['clean_alarms_per_1000'],m['ci95']['clean_alarms_per_1000'])} false reviews per 1,000 clean images; {interval(m['damage_misses_per_1000'],m['ci95']['damage_misses_per_1000'])} misses per 1,000 damaged images.",'',
            '| Assumed damaged share | False reviews / 1,000 total | Missed damage / 1,000 total | Total reviews / 1,000 |','| --- | --- | --- | --- |']
        for row in data['operational'][split]:lines.append(f"| {row['assumed_prevalence']:.0%} | {row['false_reviews_per_1000']:.1f} | {row['missed_damage_per_1000']:.1f} | {row['reviews_per_1000']:.1f} |")
        lines.append('')
    lines+=['The 1%, 5% and 20% shares are assumptions, not observed field prevalence. The site slider shows the already frozen test predictions at alternative thresholds: descriptive sensitivity only, not a new tuned operating point. Numerical threshold curves and calibration bins are stored in results.json. No dollar benefit is asserted.','',
        '## Error analysis and iteration','',
        'The gallery intentionally includes the four most confidently flagged clean examples and four lowest-scoring missed damage examples per style when available, plus class controls. These are cherry-picked to expose errors, not to estimate performance. Check the original pixels and optional synthetic truth boxes. Printing/tape, dark backgrounds, faint stains and occluded intent are plausible confounders; individual causes are hypotheses, not independently verified explanations.','',
        'Visual inspection of the error contact sheet found visible dark dent patches in test_0874 and test_0785 that the frozen model nevertheless clears; test_0023 contains a visible stain and is also missed. In shifted scenes such as shift_0618 and shift_0646, contrasting corner patches can receive near-zero damage scores. Conversely, shift_0050 is visibly an intact rendered parcel but receives a near-one score. These examples directly show that even obvious drawn damage and clean geometry are not sufficient for reliable decisions under this pipeline. They do not establish which feature caused an individual error.','',
        'The complete candidate grid and validation-only checkpoint decisions are in ITERATIONS.md and data/v2/iterations.json. The global-only and no-normalization ablations use the selected architecture and regularization; each gets its own validation-selected checkpoint, temperature and threshold. They quantify pipeline removal, not a causal effect of one weight. Six CPU fits; no GPU occupation.','',
        '## Limits and next evidence required','',
        '- No real-image test, synthetic-to-real gap, independent annotation audit or live carrier experiment. C5 remains INCONCLUSIVE.',
        '- Shared synthetic generator creates common shortcuts; more synthetic examples cannot prove real-world transfer.',
        '- The shift benchmark bundles changes and remains synthetic; it is neither an independent renderer nor a real held-out session.',
        '- Learned model predicts one binary label per single-parcel image. Damage boxes, type labels and severity are not learned outputs.',
        '- Severity is programmed contrast/extent. Partially hidden intended damage can be unobservable.',
        '- Score temperature is selected on synthetic validation. Calibration does not transfer by assumption to production prevalence.',
        '- Bootstrap intervals omit training-set uncertainty and label ambiguity. Degenerate zero-error intervals must not be read as population certainty; the JSON provides the exact one-sided zero-alarm bound where applicable.',
        '- No safe configured same-machine vision inference path was verified; no vision-model comparison was run.',
        '- Obtain a licensed, independently annotated real capture set grouped by parcel/session, use it as a new untouched test, and retrain using separate real training/validation sources before operational acceptance.','']
    (root/'REPORT.md').write_text('\n'.join(lines)+'\n')
