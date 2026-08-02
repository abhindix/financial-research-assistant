import requests
from pathlib import Path
from pypdf import PdfReader

url='https://www.sec.gov/Archives/edgar/data/320193/000032019324000016/aapl-20240330.pdf'
r=requests.get(url, timeout=120, headers={'User-Agent':'Mozilla/5.0'})
print('status', r.status_code, 'len', len(r.content))
path=Path('tmp_sec.pdf')
path.write_bytes(r.content)
reader=PdfReader(str(path))
print('pages', len(reader.pages))
text=''
for i,p in enumerate(reader.pages[:5],1):
    t=(p.extract_text() or '').strip()
    text+=t
    print('page', i, 'chars', len(t))
    print(t[:400].replace('\n',' '))
    print('---')
print('total chars', len(text))
print('metadata', reader.metadata)
