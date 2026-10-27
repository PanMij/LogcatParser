import os,tempfile,time,json
from backend.import_service import ingest
from backend.repository import connect
from backend.timeline_service import aggregate
with tempfile.TemporaryDirectory() as directory:
    os.environ['LOGCAT_DB']=directory+'/bench.sqlite'
    start=time.perf_counter()
    reports=[ingest((f'12-02 18:44:{i%60:02}.{i%1000:03} 12 34 I GameAssist: [TileHost]repeat\n' for i in range(n)),f'{n}.log',2024,'UTC') for n in [100000,40000]]
    imported=time.perf_counter()-start
    q={'file_ids':[r['id'] for r in reports],'filters':[{'tag':'GameAssist','submodules':None}]}
    start=time.perf_counter()
    with connect() as db: result=aggregate(db,q)
    assert sum(p['count'] for p in result['points'])==140000
    print(json.dumps({'lines':140000,'import_seconds':round(imported,3),'aggregate_seconds':round(time.perf_counter()-start,3),'points':len(result['points'])}))
