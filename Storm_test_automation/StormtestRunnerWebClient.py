import xmldict
import xml.dom.minidom as xmlDom
import requests
import traceback
from pprint import pprint
from PostgresDB import WebReportingDB  # @UnresolvedImport
from tools_utils import nowString  # @UnresolvedImport
import json
from urllib.parse import urlencode


class StormtestRunnerWebClient:
    '''
    classdocs
    '''
    TAMUC_IP = "10.158.2.160"
    SLOT_MONITOR_PORT = 90

    EXECUTION_CLIENT = "172.20.117.9"
    EXECUTION_CLIENT_PORT = 90

    STREAM1_IP = "172.20.116.235"
    STREAM1_SLOT_MONITOR_PORT = 90

    def __init__(self, url, port):
        '''
        Constructor
        '''
        self.url = url
        self.port = port
        self.userName = None
        self.script = None
        self.dutIds = None
        self.args = None
        self.verbose = True

    def checkSlots(self, rackID):
        if int(rackID) > 800:
            url = "http://%s:%s/rackInfo?rackid=%s" % (self.TAMUC_IP, self.SLOT_MONITOR_PORT, rackID)
        else:
            url = "http://%s:%s/rackInfo?rackid=%s" % (self.STREAM1_IP, self.STREAM1_SLOT_MONITOR_PORT, rackID)
        s = self.httpGet(url)
        rc = s.status_code
        if int(rc) == 200:
            ret = json.loads(s.content)
        else:
            ret = None
        return ret

    def httpGet(self, url, data=None):
        t = nowString()
        try:
            # print "httpGet: %s " % (url)
            timeoutSecs = 10
            if data is None:
                r = requests.get(url, timeout=timeoutSecs)
            else:
                r = requests.get(url, params=urlencode(data), timeout=timeoutSecs)
            rc = r.status_code
            if int(rc) == 200:
                print("%s httpGet: %s OK" % (t, url))
            else:
                print("%s ERROR httpGet: %s NOK status_code=%s" % (t, url, rc))
        except:
            tb = traceback.format_exc()
            print(tb)
            return None

        return r

    def postASdata(self, url, data=None):
        t = nowString()
        try:
            if self.verbose:
                # print "postASdata: %s %s" % (url, data)
                pass
            r = requests.post(url, data=data, timeout=2)
            rc = r.status_code
            if int(rc) == 200:
                if self.verbose:
                    print ("%s postASdata: %s OK" % (t, url))
                    # print r.text
            else:
                if self.verbose:
                    print ("%s postASdata: %s NOK status_code=%s" % (t, url, rc))
                    print (r.text)
                return None
        except:
            if self.verbose:
                traceback.print_exc()
            return None

        return r.text

    def getSlotIDstatus(self, slotid):
        if int(slotid) > 80000:
            url = "http://%s:%s/slotInfo?slotid=%s" % (self.TAMUC_IP, self.SLOT_MONITOR_PORT, slotid)
        else:
            url = "http://%s:%s/slotInfo?slotid=%s" % (self.STREAM1_IP, self.STREAM1_SLOT_MONITOR_PORT, slotid)
        s = self.httpGet(url)
        rc = s.status_code
        if int(rc) == 200:
            ret = json.loads(s.content)
        else:
            ret = None
        return ret

    def __runVTsued(self, userName, script, dutIds, pargs):
        url = "http://%s:%s/runTest" % (self.EXECUTION_CLIENT, self.EXECUTION_CLIENT_PORT)
        payload = {}
        payload['script'] = script
        payload['dutids'] = dutIds
        # payload['pargs'] = pargs
        pprint(payload)
        response = self.httpGet(url, payload)
        if response is None:
            return -1, None
        dd = xmldict.xml_to_dict(response.text)
        # dd = xmldict.xml_to_dict(response.text.encode("ascii", "ignore"))
        jobID = dd['html']['BODY']
        # pprint(dd)
        responseXML = '''
            <methodResponse>
            <params>
            <param>
            <value>
            <array>
            <data>
            <value>
            <i4>0</i4>
            </value>
            <value>
            <string>OK</string>
            </value>
            <value>
            <string>%s</string>
            </value>
            </data>
            </array>
            </value>
            </param>
            </params>
            </methodResponse>

        ''' % (jobID)
        xmlObj = xmlDom.parseString(responseXML)
        pretty_xml_as_string = xmlObj.toprettyxml()
        return response.status_code, pretty_xml_as_string

    def __vtSuedDUT(self, dutIds):
        webReportingDB = WebReportingDB()
        rc = webReportingDB.connect()
        if not rc:
            return

        sArray = dutIds.split(',')
        for s in sArray:
            sqlcmd = "select * from dut where dut_id = %s" % (s)
            dbRowList = webReportingDB.getDataDict(sqlcmd)
            if len(dbRowList) == 0:
                continue
            server = dbRowList[0]['server']
            if str(server).startswith("8"):
                return True

        return False

    def run(self, userName, script, dutIds, pargs):
        if self.url is None:
            print ("ERROR: url is not defined")
            return False
        if self.port is None:
            print ("ERROR: port is not defined")
            return False
        if userName is None:
            print ("ERROR: userName is not defined")
            return False
        if script is None:
            print ("ERROR: script is not defined")
            return False
        if dutIds is None:
            print ("ERROR: dutIds is not defined")
            return False

        rc = self.__vtSuedDUT(dutIds)
        if rc:
            return self.__runVTsued(userName, script, dutIds, pargs)

        self.userName = userName
        self.script = script
        self.dutIds = dutIds
        self.args = pargs

        xmlData = '''<methodCall>
      <methodName>CreateRemoteJob</methodName>
      <params>
        <param>
          <value>
            <string>##USER##</string>
          </value>
        </param>
        <param>
          <value>
            <i4>5</i4>
          </value>
        </param>
        <param>
          <value>
            <i4>##NDUTS##</i4>
          </value>
        </param>
        <param>
          <value>
            <i4>1</i4>
          </value>
        </param>
        <param>
          <value>
            <string>##ARGS##</string>
          </value>
        </param>
        <param>
          <value>
            <boolean>1</boolean>
          </value>
        </param>
        <param>
          <value>
            <array>
              <data>
                <value>
                  <string>##SCRIPT##</string>
                </value>
              </data>
            </array>
          </value>
        </param>
        <param>
          <value>
            <string />
          </value>
        </param>
        <param>
          <value>
            <array>
              <data />
            </array>
          </value>
        </param>
        <param>
          <value>
            <array>
              <data>
              ##DUTS##
              </data>
            </array>
          </value>
        </param>
      </params>
    </methodCall>'''

        dutTempl = '''<value>
          <i4>##DUTID##</i4>
        </value>
        '''

        sArray = self.dutIds.split(',')
        nDuts = len(sArray)
        duts = ""
        for s in sArray:
            d = dutTempl.replace("##DUTID##", s)
            duts = duts + d

        xmlData = xmlData.replace("##USER##", self.userName)
        xmlData = xmlData.replace("##SCRIPT##", self.script)
        xmlData = xmlData.replace("##DUTS##", duts)
        xmlData = xmlData.replace("##NDUTS##", str(nDuts))
        if self.args is None:
            xmlData = xmlData.replace("##ARGS##", "")
        else:
            xmlData = xmlData.replace("##ARGS##", self.args)
        # print xmlData

        b = bytearray(xmlData, "utf-8")
        headers = {"Content-type": "text/xml", "Content-Length": str(len(b))}

        #  conn = httplib.HTTPConnection(self.url, int(self.port))
        #  conn.request("POST", "", b, headers)
        #  response = conn.getresponse()

        url = "%s:%s" % (self.url, int(self.port))
        response = requests.post(url, data=b, headers=headers)

        print ("HTTP response status: " + str(response.status_code))
        print ("HTTP response reason: " + str(response.reason))
        # print ("----- HTTP response text -----")
        data = response.text
        # print(data)
        xmlObj = xmlDom.parseString(data)
        pretty_xml_as_string = xmlObj.toprettyxml()
        # print (pretty_xml_as_string)
        #  conn.close()
        return response.status_code, pretty_xml_as_string


def Main2():
    data = "<?xml version=\"1.0\"?><methodResponse><params><param><value><array><data><value><i4>0</i4></value><value><string>OK</string></value><value><string>19482433</string></value></data></array></value></param></params></methodResponse>"
    xmlObj = xmlDom.parseString(data)
    pretty_xml_as_string = xmlObj.toprettyxml()
    print (pretty_xml_as_string)


def Main3():
    slotid = 81107
    stWC = StormtestRunnerWebClient(None, None)
    slotInfo = stWC.getSlotIDstatus(slotid)
    slotStaus = slotInfo[0]
    print ("slotInfo: %s slotStaus=%s" % (slotInfo, slotStaus))

    pass


def Main():
    url = "tech-hv16-1"
    port = "8001"
    testing = True
    if testing:
        dutids = "12432"
        userName = "molo01"
        script = "tech/python/Ethan/watershed/ethan_watershed_18_linearTV.py"

    # print "args: [%s]" % (pargs)
    stwc = StormtestRunnerWebClient(url, int(port))
    stwc.run(userName, script, dutids, None)


if __name__ == '__main__':
    # Main3()
    Main2()
    # doTest()
