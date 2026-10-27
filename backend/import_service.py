import uuid
from .parser import parse
from .repository import connect

def ingest(stream, name, year, timezone):
    file_id = str(uuid.uuid4())
    total = failed = 0
    columns = ['timestamp','pid','tid','level','tag','submodule','message','message_body','raw_line','error']
    with connect() as db:
        batch = []
        for total, line in enumerate(stream, 1):
            row = parse(line, year, timezone)
            failed += bool(row['error'])
            batch.append([file_id,total,total] + [row.get(c) for c in columns])
            if len(batch) == 2000:
                db.executemany('INSERT INTO logs(file_id,line_number,sequence,'+','.join(columns)+') VALUES ('+','.join(['?']*13)+')', batch)
                batch.clear()
        db.executemany('INSERT INTO logs(file_id,line_number,sequence,'+','.join(columns)+') VALUES ('+','.join(['?']*13)+')', batch)
        db.execute('INSERT INTO files VALUES (?,?,?,?,?,?)',(file_id,name,year,timezone,total,failed))
    return dict(id=file_id,name=name,total=total,failed=failed)
