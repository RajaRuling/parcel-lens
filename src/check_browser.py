"""Offline evidence-flow checks and local screenshots at two viewport widths."""
import json
import os
import tempfile
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]

def main():
    directory=ROOT/'docs/screenshots';directory.mkdir(exist_ok=True)
    for name in ['.browser-home','.browser-tmp']:(ROOT/name).mkdir(exist_ok=True)
    os.environ['TMPDIR']=str(ROOT/'.browser-tmp');tempfile.tempdir=str(ROOT/'.browser-tmp')
    candidates=sorted((ROOT/'.browser-tmp/browsers').glob('chromium_headless_shell-*/chrome-headless-shell-linux64/chrome-headless-shell'))
    if not candidates:candidates=sorted((Path.home()/'.cache/ms-playwright').glob('chromium_headless_shell-*/chrome-headless-shell-linux64/chrome-headless-shell'))
    executable=os.environ.get('CHROMIUM_EXECUTABLE') or (str(candidates[-1]) if candidates else None)
    if not executable:raise RuntimeError('Install headless Chromium inside the project or set CHROMIUM_EXECUTABLE')
    data=json.loads((ROOT/'data/v2/results.json').read_text());reports=[]
    with sync_playwright() as p:
        browser=p.chromium.launch(executable_path=executable,headless=True,args=['--no-sandbox'],
            env={'HOME':str(ROOT/'.browser-home'),'TMPDIR':str(ROOT/'.browser-tmp')})
        for width in [390,1280]:
            page=browser.new_page(viewport={'width':width,'height':950},device_scale_factor=1)
            errors=[];requests=[]
            page.on('pageerror',lambda e:errors.append(str(e)));page.on('request',lambda r:requests.append(r.url))
            page.goto((ROOT/'docs/index.html').as_uri());page.wait_for_function("Boolean(document.querySelector('#scene').dataset.rendered)")
            assert page.locator('#claims-body tr').count()==5
            assert page.locator('#claims-body .supported').count()==2
            assert page.locator('#claims-body .not-supported').count()==2
            assert page.locator('#claims-body .inconclusive').count()==1
            assert page.locator('#model-body tr').count()==8
            assert page.locator('#iteration-body tr').count()==6
            assert page.locator('#model-body tr.selected').count()==1
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'),'Horizontal overflow'
            page.screenshot(path=str(directory/f'hero-{width}.png'))
            page.screenshot(path=str(directory/f'desktop-{width}.png'),full_page=True)
            page.locator('#claims').screenshot(path=str(directory/f'claims-{width}.png'))
            visited=0
            for split in ['test','shift']:
                page.locator('#split').select_option(split)
                options=page.locator('#example option');n=options.count();assert n>=12
                for i in range(n):
                    page.locator('#example').select_option(str(i))
                    expected=options.nth(i).inner_text().split(' · ')[0]
                    page.wait_for_function('(id)=>document.querySelector("#scene").dataset.rendered===id',arg=expected);visited+=1
                page.locator('#example').select_option('0')
                page.wait_for_function('(prefix)=>document.querySelector("#scene").dataset.rendered.startsWith(prefix)',arg=split+'_')
                assert 'FALSE ALARM' in page.locator('#error-explanation').inner_text()
                page.locator('#show-truth').check();page.locator('#show-truth').uncheck()
                page.locator('#next').click();assert page.locator('#example').input_value()=='1'
                page.locator('#previous').click();assert page.locator('#example').input_value()=='0'
                page.locator('#threshold').fill('0');page.locator('#threshold').dispatch_event('input')
                assert '100.0%' in page.locator('#decision-cards').inner_text()
                assert '1000.0' in page.locator('#decision-cards').inner_text()
                page.locator('#threshold').fill('0.5');page.locator('#threshold').dispatch_event('input')
                if split=='shift':
                    page.locator('#inspector').screenshot(path=str(directory/f'inspector-{width}.png'))
                    page.locator('#policy').screenshot(path=str(directory/f'policy-{width}.png'))
                matrix=page.locator('#matrix').inner_text()
                for value in data['models'][data['frozen']['winner']][split]['confusion'].values():assert str(value) in matrix
            for link in page.locator('.sources a').all():
                target=ROOT/'docs'/link.get_attribute('href');assert target.is_file(),target.name
            assert not errors,errors
            assert not any(url.startswith(('http:','https:')) for url in requests)
            reports.append({'width':width,'javascript_errors':errors,'external_requests':0,'horizontal_overflow':False,'scenes_checked':visited,
                'claims_checked':5,'models_checked':8,'splits_checked':2,'threshold_control':True,'local_evidence_links':True})
            page.close()
        browser.close()
    (directory/'browser-checks.json').write_text(json.dumps(reports,indent=2)+'\n');print(json.dumps(reports,indent=2))

if __name__=='__main__':main()
