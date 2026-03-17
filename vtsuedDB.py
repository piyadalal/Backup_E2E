

'''
Created on 12.03.2020

@author: tamuc
'''
import pymysql as MySQLdb
import datetime as dt
from pprint import pprint
import warnings


class VTsuedDB:
    '''
    classdocs
    '''

    def __init__(self):
        '''
        Constructor
        '''
        self.__connected = False

    def nowString(self):
        s = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return s

    def connectAutoDB(self):
        print("MyDB.connect() connectAutoDB()")
        self.dbHost = "homer.de.ethan.bskyb.com"
        self.dbPort = 3306
        self.dbName = "ethan_autodb"
        self.dbUser = "auto_ethan"
        self.dbPassword = "useC0nf1gFile"
        return self.__connect()

    def connect(self):
        return self.connectAutoDB()

    def connectTAMUC(self):
        print("MyDB.connect() connectTAMUC()")
        self.dbHost = "10.158.2.160"
        self.dbPort = 3306
        self.dbName = "tamuc"
        self.dbUser = "tamuc"
        self.dbPassword = "tamuc"
        return self.__connect()

    def connectSSR(self):
        self.dbHost = "10.158.2.160"
        self.dbPort = 3306
        self.dbName = "ssr"
        self.dbUser = "ssr"
        self.dbPassword = "ssr"
        return self.__connect()

    def __connect(self):
        if self.__connected:
            return self.__connected
        try:
            cnx = MySQLdb.connect(user=self.dbUser,
                                  passwd=self.dbPassword,
                                  host=self.dbHost,
                                  db=self.dbName,
                                  use_unicode=True,
                                  charset='utf8')
            cnx.autocommit(True)
        except Exception as e:
            print(e)
            return False

        warnings.filterwarnings("ignore", category=Warning)

        self.cnx = cnx
        self.database = self.dbName
        print(self.nowString() + " MySQL Connected to %s" % (self.database))
        self.__connected = True
        return self.__connected

    def sqlExec(self, sqlcmd):
        rc = True
        try:
            cursor = self.cnx.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute(sqlcmd)
        except Exception as e:
            print(("sqlExec: Something went wrong: {}".format(e)))
            rc = False

        cursor.close()
        return rc

    def getDBrows(self, sqlcmd):
        resultList = []
        try:
            cursor = self.cnx.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute(sqlcmd)
            while (1):
                row = cursor.fetchone()
                if row == None:
                    break
                resultList.append(row)

        except Exception as e:
            print(("getDataDict: Something went wrong: {}".format(e)))

        cursor.close()
        return resultList

    def addDBrow(self, table, dbRow):
        columns = list(dbRow.keys())
        values = list(dbRow.values())
        return self.insertMany(table, columns, [values])

    def insertMany(self, table, columns, valuesList):
        '''
        insert into table (col1,col2,col3,...) values (%s,%s,%s,...)
        '''
        nRecords = len(valuesList)
        print("db=%s insertMany table=%s records=%s" % (self.database, table, nRecords))
        if nRecords == 0:
            return
        strCols = ""
        strValues = ""
        rc = True
        for col in columns:
            if len(strCols) == 0:
                strCols = "%s" % (col)
                strValues = "%s"
            else:
                strCols = "%s,%s" % (strCols, col)
                strValues = "%s,%%s" % (strValues)

        sqlcmd = "insert into %s (%s) values (%s)" % (table, strCols, strValues)
        try:
            cursor = self.cnx.cursor(MySQLdb.cursors.DictCursor)
            cursor.executemany(sqlcmd, valuesList)
        except Exception as e:
            print(("insertMany: Something went wrong: {}".format(e)))
            rc = False
            for l in valuesList:
                print(l)

        cursor.close()
        return rc

    def _getVTsuedSlotInfo(self, slot_id):
        sqlcmd = '''
            SELECT   crl.slot_id          ,
                     crl.rack_id          ,
                     crl.slot_no _slot_no ,
                     crl.ip_address       ,
                     sh.mac_address ,
                     sht.hardware_type    ,
                     crl.model_version    ,
                     crl.viewing_card ,
                     svc.pin_number   ,
                     dfd.name feed    ,
                     slt.name lnb_type,
                     rl.category      ,
                     crl.functionality,
                     crl.serial_number,
                     crl.last_updated ,
                     sb.alternate_model_number _alternate_model_number
            FROM     core_rack_layout crl  ,
                     stb_viewing_card svc  ,
                     rack_slot_info rsi    ,
                     dut_feed_details dfd  ,
                     rack_layout rl        ,
                     stb_lnb_type slt      ,
                     stb_instance si       ,
                     stb_hardware sh       ,
                     stb_hardware_type sht ,
                     stb_build_instance sbi,
                     stb_build sb
            WHERE    1                         =1
            AND      crl.viewing_card          = svc.viewing_card
            AND      crl.slot_id               = rsi.slot_id
            AND      crl.slot_id               = rl.slot_id
            AND      rsi.feed_id               = dfd.id
            AND      rsi.stb_lnb_type_id       = slt.id
            AND      crl.stb_instance_id       = si.stb_instance_id
            AND      si.stb_hardware_id        = sh.stb_hardware_id
            AND      sh.stb_hardware_type_id   = sht.stb_hardware_type_id
            AND      sbi.stb_build_instance_id = si.stb_build_instance_id
            AND      sb.stb_build_id           = sbi.stb_build_id
            and crl.slot_id = %s

        ''' % (slot_id)
        rc = self.connect()
        if not rc:
            print("Connect failed")
            return None
        dbRows = self.getDBrows(sqlcmd)
        return dbRows


def getVTsuedSlotInfo(slot_id):
    myDB = VTsuedDB()
    dbRows = myDB._getVTsuedSlotInfo(slot_id)
    pprint(dbRows)
    return dbRows


def testFunc_():
    myDB = VTsuedDB()
    rc = myDB.connect()
    if not rc:
        print("Connect failed")
        return
    sqlcmd = "select * from core_rack_layout"
    dbRows = myDB.getDBrows(sqlcmd)
    pprint(dbRows)


def getServerIP(slot_id):
    myDB = VTsuedDB()
    rc = myDB.connect()
    if not rc:
        print("Connect failed")
        return
    sqlcmd = '''
        SELECT *
        FROM   rack_layout rl ,
               rack_details rd
        WHERE  1          =1
        AND    rl.rack_id = rd.rack_id
        AND    rl.slot_id = %s
    ''' % (slot_id)
    dbRows = myDB.getDBrows(sqlcmd)
    # pprint(dbRows)
    server_ip_address = dbRows[0]['server_ip_address']
    print("getServerIP: %s" % (server_ip_address))
    return server_ip_address


def updateViewingCardPIN(vc, pin):
    myDB = VTsuedDB()
    rc = myDB.connect()
    if not rc:
        print("updateViewingCardPIN: Connect failed")
        return

    sqlcmd = '''
        update stb_viewing_card set pin_number = '%s' where viewing_card = '%s'

    ''' % (pin, vc)
    rc = myDB.sqlExec(sqlcmd)
    print("updateViewingCardPIN(%s,%s) = %s " % (vc, pin, rc))
    return rc


if __name__ == '__main__':
    slot_id = 81705
    dbRow = getVTsuedSlotInfo(slot_id)
    pprint(dbRow)
    rc = updateViewingCardPIN("30000145204673", "1111")
    pprint(rc)
