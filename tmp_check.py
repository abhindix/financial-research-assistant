import io
import requests
from pypdf import PdfWriter

buf = io.BytesIO()
writer = PdfWriter()
writer.add_blank_page(width=72, height=72)
writer.write(buf)
data = buf.getvalue()
resp = requests.post('http://127.0.0.1:8002/api/v1/documents', files={'file': ('sample.pdf', data, 'application/pdf')}, timeout=60)
print(resp.status_code)
print(resp.text)
