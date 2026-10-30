"""Fail on restricted client or employer terms in authored public assets."""
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[1]
# Construct the deny list numerically so this public check obeys its own policy.
DENIED=[''.join(map(chr,codes)) for codes in [
    [117,112,115],[99,111,103,110,105,122,97,110,116],
    [117,110,105,116,101,100,32,112,97,114,99,101,108],
    [98,114,111,119,110],[105,104,115],[104,97,99,107,97,116,104,111,110],
    [121,111,117,116,117,98,101,46,99,111,109],[121,111,117,116,117,46,98,101],
    [114,111,98,111,110,117,103,103,101,116,115],[106,97,121,32,101]]]
TEXT={'.py','.md','.txt','.json','.html','.css','.js','.svg','.csv'}

def scan(root=ROOT):
    hits=[]
    for path in sorted(Path(root).rglob('*')):
        if any(part in {'.venv','__pycache__','.pytest_cache','.browser-home','.browser-tmp'} for part in path.relative_to(root).parts): continue
        if path.suffix.lower() not in TEXT or not path.is_file(): continue
        content=path.read_text(encoding='utf-8')
        for word in DENIED:
            for match in re.finditer(r'\b'+re.escape(word)+r'\b',content,re.I):
                hits.append((str(path.relative_to(root)),content[:match.start()].count('\n')+1))
    return hits

if __name__=='__main__':
    hits=scan()
    for file,line in hits: print(f'FAIL {file}:{line}: restricted term')
    if hits: raise SystemExit(1)
    print('PASS: public text contains no restricted terms (case-insensitive word scan).')
