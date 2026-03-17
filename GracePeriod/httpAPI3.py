# Created on 12.10.2022
# @author: molo01

import requests
from urllib.parse import urlencode
import traceback
import websocket
import json

class HTTPapi3:
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
            print("HTTPapi.httpGet: {} timeout={}".format(url, self.__requestTimeout))
            if data is None:
                r = requests.get(url, timeout=self.__requestTimeout)
            else:
                r = requests.get(url, params=urlencode(data), timeout=self.__requestTimeout)
            rc = r.status_code
            if int(rc) == 200:
                self.__logging("HTTPapi.httpGet: {} OK".format(url))
                self.__logging("{}".format(r.text))
                s = r.text.strip()
            else:
                self.__logging("HTTPapi.httpGet: {} NOK status_code={}".format(url, rc), True)
                self.__logging("{}".format(r.text))
                s = None
            return s
        except:
            tb = traceback.format_exc()
            self.__logging(tb, True)
            return None

    def httpPost(self, url, data=None, json=None):
        try:
            self.__logging("httpPost: url={} data={} json={}".format(url, data, json))
            r = requests.post(url, params=urlencode(data), json=json, timeout=5)
            rc = r.status_code
            if int(rc) == 200:
                self.__logging("httpPost: {} OK".format(url))
                self.__logging("{}".format(r.text))
            else:
                self.__logging("httpPost: {} NOK status_code={}".format(url, rc), True)
                self.__logging("{}".format(r.text))
                return False
        except:
            tb = traceback.format_exc()
            self.__logging(tb, True)
            return None

        return True

    def getWSdata(self, url):
        dataDict = None
        print("getWSdata: url={}".format(url))
        try:
            # print url
            socket = websocket.create_connection(url, timeout=5)
            raw_data = socket.recv()
            socket.close()
            dataDict = json.loads(raw_data)
        except:
            traceback.print_exc()
            return None

        print("getWSdata: {}".format(dataDict))
        return dataDict


if __name__ == '__main__':
    pass
