from .filter_service import where

def aggregate(db, query):
    clause, args = where(query)
    bounds = db.execute('SELECT min(timestamp),max(timestamp) FROM logs WHERE '+clause,args).fetchone()
    if bounds[0] is None: return {'bucket_ms':1,'points':[]}
    groups = db.execute('SELECT count(*) FROM (SELECT tag,submodule FROM logs WHERE '+clause+' GROUP BY tag,submodule)',args).fetchone()[0]
    width = max(int(query.get('bucket_ms') or 1), 1)
    while True:
        size = db.execute('SELECT count(*) FROM (SELECT timestamp / ?,tag,submodule FROM logs WHERE '+clause+' GROUP BY timestamp / ?,tag,submodule)', [width]+args+[width]).fetchone()[0]
        if size <= max(2000, groups): break
        width *= 10
    rows = db.execute('SELECT (timestamp / ?) * ? AS time, tag,submodule,count(*) AS count FROM logs WHERE '+clause+' GROUP BY time,tag,submodule ORDER BY time,tag,submodule',[width,width]+args)
    return {'bucket_ms':width,'points':[dict(r) for r in rows]}
