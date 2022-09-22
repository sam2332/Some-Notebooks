import sqlite3, os


class Sqler:
    def __init__(self, basePath, debug=False):
        self.debug = debug
        self.base_path = basePath
        self.closed = True
        self.created = os.path.exists(self.base_path)

    def dict_factory(self, cursor, row):
        d = {}
        for idx, col in enumerate(cursor.description):
            d[col[0]] = row[idx]
        return d

    def close(self):
        if not self.closed:
            self.cursor.close()
            self.conn.close()
            self.closed = True

    def connect(self):
        if self.closed:
            self.conn = sqlite3.connect(self.base_path)
            self.conn.row_factory = self.dict_factory
            self.cursor = self.conn.cursor()
            self.closed = False

    def query(self, query, param=()):
        if self.debug:
            print(query, param)
        if self.closed:
            self.connect()
        data = self.cursor.execute(query, param)
        if 'insert' in query.lower() or 'update' in query.lower():
            self.conn.commit()
        return self.cursor

    def tableExists(self, table_name):
        if self.closed:
            self.connect()
        self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        for table in self.cursor.fetchall():
            if table['name'] == table_name:
                return True
        return False

    def createTable(self, table_name, table_def):
        sql = 'CREATE TABLE ' + table_name + ' ('
        first = True
        for item in table_def:
            if not first:
                sql += ','
            else:
                first = False
            sql += item + " " + table_def[item]
        sql += ')'
        self.cursor.execute(sql)
        self.conn.commit()


class KV_Sqler:
    def __init__(self, basePath, table):
        self.db = Sqler(basePath)
        self.table = table
        if not self.db.tableExists(table):
            self.db.createTable(table, {"key": "text", "value": "text"})

    def __setitem__(self, key, value):
        t = (key,)
        self.db.query("delete from {} where key = ?;".format(self.table), t)
        t = (key, value)
        self.db.query("INSERT INTO {} (key,value) VALUES (?,?);".format(self.table), t)
        self.db.close()

    def __getitem__(self, key):
        t = (key,)
        data = self.db.query(
            "select value from " + self.table + " WHERE key=?", t
        ).fetchone()
        self.db.close()
        return data['value']

    def getAll(self):
        return self.db.query("select * from " + self.table).fetchall()

    def getAllKeys(self):
        return self.db.query("select key from " + self.table).fetchall()

'''
def Demo_KV_Sqler_Demo():
    k = KV_Sqler("Squirrel.db", 'KeyValues')
    k.getAllKeys()

    k['myKey'] = 'testing'

    k['myKey']


def Demo_Sqler_Demo():

    s = Sqler("Squirrel.db")
    from datetime import datetime

    if not s.tableExists("stocks"):
        print("createing stocks")
        s.createTable(
            'stocks',
            {
                "date": "text",
                "trans": "text",
                "symbol": "text",
                "qty": "real",
                "price": "real",
            },
        )
        t = (datetime.now(), "Buy", "GOOG", 1, 909)
        for i in range(50):
            t = (datetime.now(), "Buy", "GOOG", 1 + i, 909)
            s.query('INSERT INTO stocks VALUES (?,?,?,?,?)', t)
        s.close()

    t = ('GOOG',)
    s.query('SELECT * FROM stocks WHERE symbol=?', t).fetchall()

    import requests

    from datetime import datetime

    if not s.tableExists("covid"):
        print("creating covid")
        s.createTable('covid', {"date": "datetime", "state": "text", "qty": "real"})

    res = requests.get("https://covidtracking.com/api/states")
    covid = res.json()

    for state in covid:
        t = (
            datetime.strptime(str(state['date']), "%Y%m%d"),
            state['state'],
            state["positive"],
        )
        s.query('INSERT INTO covid VALUES (?,?,?)', t)
    s.close()

    s.query('SELECT * FROM covid group by state, date;').fetchall()

    s.close()
'''