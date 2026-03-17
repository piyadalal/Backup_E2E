
import socket
import psycopg2 as pg
import psycopg2.extras as extras
import datetime as dt


class WebReportingDB:
    '''
    classdocs
    '''

    def __init__(self):
        '''
        Constructor
        '''
        self.connected = False

    def nowString(self):
        s = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return s

    def connectSoakroom(self):
        sHostname = socket.gethostname()
        if sHostname == "vdc-vm-0005555":
            dbHost = "127.0.0.1"
        else:
            dbHost = "vdc-vm-0005555"
        self.__dbPort = 5432
        self.__dbHost = dbHost

        # self.__dbHost = "10.158.2.170"
        # self.__dbPort = 15432
        self.__database = "soak_room"
        self.__dbUser = "soakroom"
        self.__dbPassword = "soakroom"
        return self.__connect()

    def connectStormtest(self):
        self.__dbHost = "tech-hv16-1"
        self.__dbPort = 5432
        # self.__dbHost = "10.158.2.170"
        # self.__dbPort = 15432
        self.__database = "stormtest"
        self.__dbUser = "stormtest"
        self.__dbPassword = "stormtest"
        return self.__connect()

    def connectStormtest2(self):
        self.__dbHost = "172.20.117.9"
        self.__dbPort = 5432
        self.__database = "stormtest"
        self.__dbUser = "stormtest"
        self.__dbPassword = "stormtest"
        return self.__connect()

    def connect(self):
        return self.connectSoakroom()

    def __connect(self):
        if self.connected:
            return True
        try:
            conn = pg.connect(
                "host='%s' port=%s dbname='%s' user='%s' password='%s'" % (
                    self.__dbHost, self.__dbPort, self.__database, self.__dbUser, self.__dbPassword
                ))
            conn.autocommit = True
        except pg.Error as err:
            print(err)
            return False

        self.cnx = conn
        print ("PostgreSQL Connected ", self.__dbHost, self.__dbPort, self.__database)
        self.connected = True
        return True

    def getDataDict(self, sqlcmd):
        select_statement = sqlcmd
        resultList = []
        try:
            cursor = self.cnx.cursor(cursor_factory=extras.DictCursor)
            cursor.execute(select_statement)
            colnames = [desc[0] for desc in cursor.description]
            while (1):
                row = cursor.fetchone()
                if row == None:
                    break
                rowDict = {}
                for i in range(len(colnames)):
                    rowDict[colnames[i]] = row[i]
                resultList.append(rowDict)

        except pg.Error as err:
            print("getDataDict: Something went wrong: {}".format(err))

        cursor.close()
        return resultList

    def addDataDict(self, table, dataDict):
        insert_statement = "INSERT INTO  %s (%s) VALUES (%s)"
        cols = ""
        vals = ""
        valueList = []
        try:
            cursor = self.cnx.cursor(cursor_factory=extras.DictCursor)
            for key, value in dataDict.iteritems():
                if (key == "id"):
                    continue
                valueList.append(value)
                if len(cols) == 0:
                    cols = cols + key
                    vals = "%s"
                else:
                    cols = cols + "," + key
                    vals = vals + "," + "%s"

            cursor.execute(insert_statement % (table, cols, vals), valueList)

        except pg.Error as err:
            print("addDataDict: Something went wrong: {}".format(err))
            return False

        cursor.close()
        return True

    def sqlExec(self, sqlcmd):
        rc = True
        try:
            cursor = self.cnx.cursor(cursor_factory=extras.DictCursor)
            cursor.execute(sqlcmd)
        except pg.Error as err:
            print("sqlExec: Something went wrong: {}".format(err))
            rc = False

        cursor.close()
        return rc


if __name__ == '__main__':
    pass
