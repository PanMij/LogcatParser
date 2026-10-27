import io
import os
import tempfile
import unittest
from backend.parser import parse
from backend.import_service import ingest
from backend.repository import connect
from backend.filter_service import where
from backend.timeline_service import aggregate

class ParserTests(unittest.TestCase):
    def test_prefix(self):
        for message,sub,body in [('[TileHost]refresh()','TileHost','refresh()'),('[GameScreensaver.Power]x','GameScreensaver.Power','x'),('normal [middle]',None,'normal [middle]'),('[]x',None,'[]x'),('[A][B]x','A','[B]x')]:
            r=parse('12-02 18:44:43.211 17259 19363 I GameAssist   :   '+message,2024,'UTC')
            self.assertEqual((r['tag'],r['submodule'],r['message_body']),('GameAssist',sub,body))
            self.assertEqual(r['message'],message)
    def test_invalid(self):
        for line in [' at java.lang.Foo(x:1)','12-02 18:44','garbage','02-30 00:00:00.000 1 2 I X: x']:
            self.assertTrue(parse(line,2024,'UTC')['error'])
    def test_time(self):
        s='12-02 18:44:43.211 1 2 E X: x'
        self.assertEqual(parse(s,2024,'UTC')['timestamp']-parse(s,2024,'Asia/Shanghai')['timestamp'],8*3600000)
        self.assertNotEqual(parse(s,2024,'UTC')['timestamp'],parse(s,2025,'UTC')['timestamp'])

class QueryTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.old=os.environ.get('LOGCAT_DB');os.environ['LOGCAT_DB']=self.tmp.name+'/test.sqlite'
        lines=['01-01 00:00:01.000 1 2 I A: [X]one','01-01 00:00:01.000 1 2 E A: [Y]two','01-01 00:00:00.000 1 2 W A: plain','01-01 00:00:01.000 1 2 I B: [X]three',' at stack']
        self.report=ingest(io.StringIO('\n'.join(lines)),'sample.log',2024,'UTC');self.q={'file_ids':[self.report['id']],'filters':[{'tag':'A','submodules':None},{'tag':'B','submodules':None}]}
    def tearDown(self):
        if self.old is None:os.environ.pop('LOGCAT_DB',None)
        else:os.environ['LOGCAT_DB']=self.old
        self.tmp.cleanup()
    def count(self,q):
        c,a=where(q)
        with connect() as db:return db.execute('SELECT count(*) FROM logs WHERE '+c,a).fetchone()[0]
    def test_filters(self):
        for filters,n in [([],0),([{'tag':'A','submodules':None}],3),([{'tag':'A','submodules':[None]}],1),([{'tag':'A','submodules':[]}],0),([{'tag':'A','submodules':['X','Y']}],2),([{'tag':'A','submodules':['Y']},{'tag':'B','submodules':['X']}],2),([{'tag':'X','submodules':['A']}],0)]:
            self.assertEqual(self.count({**self.q,'filters':filters}),n)
        self.assertEqual(self.count({**self.q,'levels':['I']}),2)
        self.assertEqual(self.count({**self.q,'keyword':'one'}),1)
    def test_timeline(self):
        with connect() as db:
            for width in [1,1000,60000]:
                result=aggregate(db,{**self.q,'bucket_ms':width});self.assertEqual(sum(p['count'] for p in result['points']),4)
            result=aggregate(db,self.q);point=result['points'][0]
            self.assertEqual(self.count({**self.q,'start':point['time'],'end':point['time']+result['bucket_ms']-1}),1)
    def test_preservation(self):
        self.assertEqual((self.report['total'],self.report['failed']),(5,1))
        with connect() as db:
            rows=db.execute('SELECT * FROM logs ORDER BY sequence').fetchall()
            self.assertEqual([r['line_number'] for r in rows],[1,2,3,4,5]);self.assertLess(rows[2]['timestamp'],rows[0]['timestamp']);self.assertEqual(rows[0]['timestamp'],rows[1]['timestamp'])
    def test_api(self):
        from fastapi.testclient import TestClient
        from backend.api import app
        with TestClient(app) as client:
            self.assertEqual(client.post('/api/logs',json=self.q).json()['total'],4)
            self.assertEqual(len(client.get('/api/errors/'+self.report['id']).json()),1)
            self.assertEqual(len(client.post('/api/export/json',json=self.q).json()),4)
            record=client.post('/api/logs',json=self.q).json()['rows'][0]
            self.assertEqual(len(client.get('/api/context/'+str(record['id'])).json()),5)

if __name__=='__main__':unittest.main()
