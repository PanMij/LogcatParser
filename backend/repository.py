import os
import sqlite3

def connect():
    db = sqlite3.connect(os.environ.get('LOGCAT_DB', 'logcat.sqlite'), timeout=60)
    db.row_factory = sqlite3.Row
    db.executescript('''
    PRAGMA journal_mode=WAL;
    CREATE TABLE IF NOT EXISTS files(id TEXT PRIMARY KEY,name TEXT,year INTEGER,timezone TEXT,total INTEGER,failed INTEGER);
    CREATE TABLE IF NOT EXISTS logs(id INTEGER PRIMARY KEY,file_id TEXT,line_number INTEGER,sequence INTEGER,
      timestamp INTEGER,pid INTEGER,tid INTEGER,level TEXT,tag TEXT,submodule TEXT,message TEXT,message_body TEXT,raw_line TEXT,error TEXT);
    CREATE INDEX IF NOT EXISTS log_time ON logs(file_id,timestamp,id);
    CREATE INDEX IF NOT EXISTS log_modules ON logs(file_id,tag,submodule,timestamp);
    CREATE INDEX IF NOT EXISTS log_source ON logs(file_id,line_number);
    ''')
    return db
