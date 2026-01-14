import psycopg2
from urllib.parse import urlparse
import os

DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql+asyncpg://root:root@localhost:5432/chicmic')
parsed = urlparse(DATABASE_URL)
dsn = {
    'dbname': parsed.path.lstrip('/') or '',
    'user': parsed.username,
    'password': parsed.password,
    'host': parsed.hostname,
    'port': parsed.port,
}
print('Connecting with DSN:', dsn)
conn = psycopg2.connect(**dsn)
cur = conn.cursor()
cur.execute('SELECT id, file_name, total_rows, inserted_rows, status, created_at FROM ingests ORDER BY created_at DESC LIMIT 10')
ings = cur.fetchall()
print('Recent ingests:')
for r in ings:
    print(r)

cur.execute('SELECT count(*) FROM logs')
print('Total logs rows:', cur.fetchone()[0])

cur.execute('SELECT id, ingest_id, timestamp, module, level, message FROM logs ORDER BY id DESC LIMIT 10')
rows = cur.fetchall()
print('Recent log rows:')
for row in rows:
    print(row)

cur.close()
conn.close()
