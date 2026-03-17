'''
Created on 12.10.2022

@author: molo01
'''
import requests
from urllib import urlencode
import traceback
import websocket
import json

class HTTPapi:
    def __init__(self):
        self.logger = None
        self.__requestTimeout = 5

    def __logging(self, msg, errorMsg=False):
        if self.logger is None:
            if errorMsg:
                print("ERROR: ", msg)
            else:
                print(msg)
        else:
            if errorMsg:
                self.logger.error(msg)
            else:
                self.logger.debug(msg)


    def httpGet(self, url, data=None):
        try:
            print("HTTPapi.httpGet: %s timeout=%s" % (url, self.__requestTimeout))
            if data is None:
                r = requests.get(url, timeout=self.__requestTimeout)
            else:
                r = requests.get(url, params=urlencode(data), timeout=self.__requestTimeout)
            rc = r.status_code
            if int(rc) == 200:
                self.__logging("HTTPapi.httpGet: %s OK" % (url))
                self.__logging("%s" % (r.text))
                s = r.text.strip()
            else:
                self.__logging("HTTPapi.httpGet: %s NOK status_code=%s" % (url, rc), True)
                self.__logging("%s" % (r.text))
                s = None
            return s
        except:
            tb = traceback.format_exc()
            self.__logging(tb, True)
            return None


    def httpPost(self, url, data=None, json=None):
        try:
            self.__logging("httpPost: url=%s data=%s json=%s" % (url, data, json))
            r = requests.post(url, params=urlencode(data), json=json, timeout=5)
            rc = r.status_code
            if int(rc) == 200:
                self.__logging("httpPost: %s OK" % (url))
                self.__logging("%s" % (r.text))
            else:
                self.__logging("httpPost: %s NOK status_code=%s" % (url, rc), True)
                self.__logging("%s" % (r.text))
                return False
        except:
            tb = traceback.format_exc()
            self.__logging(tb, True)
            return None

        return True


    def getWSdata(self, url):
        dataDict = None
        print("getWSdata: url=%s" % (url))
        try:
            # print url
            socket = websocket.create_connection(url, timeout=5)
            raw_data = socket.recv()
            socket.close()
            dataDict = json.loads(raw_data)
        except:
            traceback.print_exc()
            return None

        print("getWSdata: %s" % (dataDict))
        return dataDict


if __name__ == '__main__':
    pass
