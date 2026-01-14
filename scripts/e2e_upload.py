import httpx
import time

API = "http://127.0.0.1:8000"
SAMPLE = "error_logs_C1.txt"

print('Using sample file:', SAMPLE)
with open(SAMPLE, 'rb') as f:
    files = {'file': (SAMPLE, f, 'text/plain')}
    print('Posting to /upload...')
    r = httpx.post(API + '/upload', files=files, timeout=30.0)
    print('Status:', r.status_code)
    try:
        print('Response JSON:', r.json())
    except Exception:
        print('Response text:', r.text)

# wait a moment for ingest to be persisted
print('Waiting 1s for ingest to settle...')
time.sleep(1)
print('Querying /api/ingests')
r2 = httpx.get(API + '/api/ingests', timeout=10.0)
print('ingests status:', r2.status_code)
try:
    ingests = r2.json()
    print('Found', len(ingests), 'ingests')
    if ingests:
        latest = ingests[0]
        print('Latest ingest id:', latest.get('id'))
        lid = latest.get('id')
        print('Querying logs for latest ingest...')
        r3 = httpx.get(API + f'/api/ingests/{lid}/logs?limit=10', timeout=10.0)
        print('/logs status:', r3.status_code)
        try:
            logs = r3.json()
            print('First', min(10, len(logs)), 'log rows:')
            for row in logs[:10]:
                print(row)
        except Exception:
            print('Logs response text:', r3.text)
except Exception:
    print('Failed to parse /api/ingests response:', r2.text)

print('Done')
