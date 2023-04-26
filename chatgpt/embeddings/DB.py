import pytds
class ITSMDB_Context():
    """AutoMapper| name:ITSM_DB """
    def __enter__(self):
        self.conn = pytds.connect(
            "ITSMDB",
            "BSC_4_0",
            user='bossadmin',
            password='The sauce is the boss.',
            as_dict=True,
        )
        self.cur  = self.conn.cursor()
        return self.cur
    def __exit__(self,s,a,v):
        self.cur.close()
        self.conn.close()