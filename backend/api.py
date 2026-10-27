import csv
import io
import json
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import StreamingResponse
from .repository import connect
from .import_service import ingest
from .filter_service import where
from .timeline_service import aggregate

app = FastAPI(title='Logcat Analyzer')
@app.post('/api/import')
def upload(file: UploadFile = File(...), year: int = Form(...), timezone: str = Form(...)):
    if not 1 <= year <= 9999: raise HTTPException(422,'Invalid year')
    try: ZoneInfo(timezone)
    except ZoneInfoNotFoundError: raise HTTPException(422,'Invalid timezone')
    if not (file.filename or '').lower().endswith(('.txt','.log')): raise HTTPException(422,'Expected .txt or .log')
    return ingest(io.TextIOWrapper(file.file,encoding='utf-8',errors='replace'),file.filename,year,timezone)
@app.get('/api/files')
def files():
    with connect() as db: return [dict(r) for r in db.execute('SELECT * FROM files')]
@app.post('/api/tree')
def tree(q: dict):
    ids=q.get('file_ids',[])
    if not ids: return []
    with connect() as db:
        return [dict(r) for r in db.execute('SELECT tag,submodule,count(*) AS count FROM logs WHERE timestamp IS NOT NULL AND file_id IN ('+','.join('?' for _ in ids)+') GROUP BY tag,submodule ORDER BY tag,submodule',ids)]
@app.post('/api/logs')
def logs(q: dict):
    clause,args=where(q)
    with connect() as db:
        total=db.execute('SELECT count(*) FROM logs WHERE '+clause,args).fetchone()[0]
        rows=db.execute('SELECT * FROM logs WHERE '+clause+' ORDER BY timestamp,file_id,sequence LIMIT ? OFFSET ?',args+[min(200,max(1,int(q.get('limit',100)))),max(0,int(q.get('offset',0)))])
        return {'total':total,'rows':[dict(r) for r in rows]}
@app.post('/api/timeline')
def timeline(q: dict):
    with connect() as db: return aggregate(db,q)
@app.post('/api/stats')
def stats(q: dict):
    clause,args=where(q)
    with connect() as db:
        return [dict(r) for r in db.execute('SELECT tag,level,count(*) AS count FROM logs WHERE '+clause+' GROUP BY tag,level',args)]
@app.get('/api/context/{record_id}')
def context(record_id: int):
    with connect() as db:
        r=db.execute('SELECT * FROM logs WHERE id=?',(record_id,)).fetchone()
        if r is None: raise HTTPException(404)
        return [dict(x) for x in db.execute('SELECT * FROM logs WHERE file_id=? AND line_number BETWEEN ? AND ? ORDER BY line_number',(r['file_id'],r['line_number']-10,r['line_number']+10))]
@app.get('/api/errors/{file_id}')
def errors(file_id: str, offset: int=0):
    with connect() as db: return [dict(r) for r in db.execute('SELECT * FROM logs WHERE file_id=? AND error IS NOT NULL ORDER BY line_number LIMIT 100 OFFSET ?',(file_id,max(0,offset)))]
@app.post('/api/export/{format}')
def export(format: str,q: dict):
    if format not in ('csv','json'): raise HTTPException(422)
    clause,args=where(q)
    def stream():
        with connect() as db:
            cursor=db.execute('SELECT * FROM logs WHERE '+clause+' ORDER BY timestamp,file_id,sequence',args)
            if format=='json':
                yield '['
                for i,r in enumerate(cursor): yield (',' if i else '')+json.dumps(dict(r),ensure_ascii=False)
                yield ']'
            else:
                buffer=io.StringIO(); writer=csv.writer(buffer)
                writer.writerow([c[0] for c in cursor.description]); yield buffer.getvalue()
                for r in cursor:
                    buffer.seek(0);buffer.truncate();writer.writerow(list(r));yield buffer.getvalue()
    return StreamingResponse(stream(),media_type='application/json' if format=='json' else 'text/csv',headers={'Content-Disposition':f'attachment; filename="logs.{format}"'})
