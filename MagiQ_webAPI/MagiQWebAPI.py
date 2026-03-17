
'''
Created on 22.03.2022

@author: MOLO01
'''

import os
from vtsuedDB import VTsuedDB  # @UnresolvedImport
from pprint import pprint, pformat
import datetime as dt
import time as ti
import requests
import traceback
import json
from urllib.parse import quote_plus
from io import BytesIO
import websocket
from PIL import Image

from imageManager import ImageManager  # @UnresolvedImport
import base64


class MagiqWebAPI:

    def __init__(self):
        self.slotid = -1
        self.redratFile = None
        self.logpath = None
        self.logger = None
        self.__verbose = False
        self.__autoDB = None
        self.__lockToken = None
        self.__streamID = None
        self.__rackIP = None
        self.__rackid = -1
        self.__slotno = -1
        # Stormtest ClientAPI
        self.__api = None
        self.__imageManager = ImageManager()

        self.__useProxies = False
        self.__proxies = {
            'http': 'http://172.20.117.9:2000',
            'https': 'http://172.20.117.9:2000'
        }

    def __getProxy(self):
        if self.__useProxies:
            return self.__proxies
        else:
            return None

    def setStormtestAPI(self, api):
        self.__api = api

    def __saveSTIO(self, fn):
        if self.__api is None:
            self.__logging("Stormtest API is not defined")
            return

        tmpFile = "%s_x" % (fn)
        os.rename(fn, tmpFile)
        stio = self.__api.Imaging.ImageFromFile(tmpFile)
        stio.Save(fn)
        stio.Close()
        os.unlink(tmpFile)
        last_fn = stio.GetLastSavedName()
        self.__logging("MagiqWebAPI.__saveSTIO: %s -- %s" % (os.path.basename(fn), os.path.basename(last_fn)))

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

    def __getNASurl(self, fn):
        import socket
        h = socket.gethostname()
        # print "__getNASurl: hostname=%s" % (h)
        executionServers = ["tamuc06"]
        if h not in executionServers:
            return fn
        unixFN = fn.replace("\\", "/")
        unixFN = unixFN.replace("//172.20.116.70/log-file", "http://172.20.116.70:8091/logs")
        return unixFN

    def __dbConnect(self):
        rc = True
        if self.__autoDB is None:
            self.__autoDB = VTsuedDB()
            self.__autoDB.logger = self.logger
            rc = self.__autoDB.connect()
        return rc

    def __wsGet(self, url, jsonStr=None, useLockToken=False):
        headers = {"X-Magiq-Lock-Token": self.__lockToken}
        # verbose = self.__verbose
        verbose = True
        raw_data = None
        socket = None
        try:
            if verbose:
                self.__logging("__wsGet: %s " % (url))
            if useLockToken:
                socket = websocket.create_connection(url, timeout=5, header=headers)
            else:
                socket = websocket.create_connection(url, timeout=5)
            socket.settimeout(5)
            if jsonStr:
                socket.send(jsonStr)
            raw_data = socket.recv()
        except websocket.WebSocketTimeoutException:
            self.__logging("__wsGet: WebSocketTimeoutException", True)
        except:
            tb = traceback.format_exc()
            self.__logging("__wsGet\n%s" % (tb), True)

        if socket:
            socket.close()
            socket = None

        if verbose:
            self.__logging("__wsGet: %s" % (raw_data))
        return raw_data

    def __postRequest(self, url, data=None, json=None):
        headers = {"X-Magiq-Lock-Token": self.__lockToken}
        verbose = self.__verbose
        responseText = None
        try:
            if verbose:
                self.__logging("__postRequest: %s " % (url))
            r = requests.post(url, data=data, json=json, timeout=5, headers=headers, proxies=self.__getProxy())
            rc = r.status_code
            if int(rc) == 200:
                self.__logging("__postRequest: %s OK" % (url))
                responseText = r.text
            else:
                self.__logging("__postRequest: %s NOK status_code=%s %s" % (url, rc, r.text))
        except:
            tb = traceback.format_exc()
            self.__logging("__postRequest\n%s" % (tb), True)

        if verbose:
            self.__logging("__postRequest: %s" % (responseText))
        return responseText

    def __ocrPostRequest(self, url, imageFilename):
        imageFile = {'img': open(imageFilename, "rb")}
        verbose = self.__verbose
        responseText = None
        try:
            if verbose:
                self.__logging("__ocrPostRequest: %s " % (url))
            r = requests.post(url, files=imageFile, timeout=5, proxies=self.__getProxy())
            rc = r.status_code
            if int(rc) == 200:
                self.__logging("__ocrPostRequest: %s OK" % (url))
                responseText = r.text
            else:
                self.__logging("__ocrPostRequest: %s NOK status_code=%s" % (url, rc))
        except:
            tb = traceback.format_exc()
            self.__logging("__ocrPostRequest\n%s" % (tb), True)

        if verbose:
            self.__logging("__ocrPostRequest: %s" % (responseText))
        return responseText

    def __getRequest(self, url):
        verbose = self.__verbose
        responseText = None
        try:
            if verbose:
                self.__logging("__getRequest: %s " % (url))
            r = requests.get(url, timeout=5, proxies=self.__getProxy())
            rc = r.status_code
            if int(rc) == 200:
                self.__logging("__getRequest: %s OK" % (url))
                responseText = r.text
            else:
                self.__logging("__getRequest: %s NOK status_code=%s" % (url, rc))
        except:
            tb = traceback.format_exc()
            self.__logging("__getRequest\n%s" % (tb), True)

        if verbose:
            self.__logging("__getRequest: %s" % (responseText))
        return responseText

    def __putRequest(self, url):
        headers = {"X-Magiq-Lock-Token": self.__lockToken}
        verbose = self.__verbose
        responseText = None
        try:
            if verbose:
                self.__logging("__putRequest: %s " % (url))
            r = requests.put(url, timeout=5, headers=headers, proxies=self.__getProxy())
            rc = r.status_code
            if int(rc) == 200:
                self.__logging("__putRequest: %s OK" % (url))
                responseText = r.text
            else:
                self.__logging("__putRequest: %s NOK status_code=%s" % (url, rc))
        except:
            tb = traceback.format_exc()
            self.__logging("__putRequest\n%s" % (tb), True)

        if verbose:
            self.__logging("__putRequest: %s" % (responseText))
        return responseText

    def __deleteRequest(self, url, token):
        headers = {"X-Magiq-Lock-Token": token}
        verbose = self.__verbose
        responseText = None
        try:
            if verbose:
                self.__logging("__deleteRequest: %s " % (url))
            r = requests.delete(url, timeout=5, headers=headers, proxies=self.__getProxy())
            rc = r.status_code
            if int(rc) == 200:
                self.__logging("__deleteRequest: %s OK" % (url))
                responseText = r.text
            else:
                self.__logging("__deleteRequest: %s NOK status_code=%s" % (url, rc))
        except:
            tb = traceback.format_exc()
            self.__logging("__deleteRequest\n%s" % (tb), True)

        if verbose:
            self.__logging("__deleteRequest: %s" % (responseText))
        return responseText

    def __getRackDetails(self):
        rc = self.__dbConnect()
        if not rc:
            return None

        sqlcmd = "select * from rack_details where 1=1 and rack_id = %s" % (self.__rackid)
        dbRowlist = self.__autoDB.getDBrows(sqlcmd)
        # pprint(dbRowlist)
        return dbRowlist[0]

    def __getRackIP(self):
        dbRow = self.__getRackDetails()
        ip = dbRow['server_ip_address']
        return ip

    def __getBaseURL(self, protocol="http", port=8080):
        u = "%s://%s:%s" % (protocol, self.__rackIP, port)
        return u

    def __getRMbaseURL(self):
        u = "http://10.158.4.165:15020"
        return u

    def __secs2hms(self, secs):
        '''
        convert seconds to time format %H:%M:%S
        '''
        a = str(dt.timedelta(seconds=secs))
        if len(a) == 7:
            a = "0" + a
        return a

    def __loadSlotDetails(self, slotid):
        rackid, slotno = divmod(int(slotid), 100)
        self.__rackid = rackid
        self.__slotno = slotno
        self.slotid = slotid
        self.__rackIP = self.__getRackIP()

    def getSlotLockInfo(self, slotid):
        '''
        [1, 'StormTestUser', '.NET Client Version 3.5.7996.18733']
        [0, '', '']
        '''
        self.__logging("getSlotLockInfo: %s" % (slotid))
        self.__loadSlotDetails(slotid)

        sessionLock = self.sessionLockExists()
        if sessionLock:
            retArray = [1, "sessionLock", "Locked by Web User or Resource Manager"]
            self.__logging("getSlotLockInfo: retArray=%s" % (retArray))
            return retArray

        baseURL = self.__getBaseURL()
        u = "/v1/%s/lock" % (self.__slotno)
        url = "%s%s" % (baseURL, u)
        jsonStr = self.__getRequest(url)
        jsonDict = json.loads(jsonStr)
        self.__logging("getSlotLockInfo: %s" % (pformat(jsonDict)))

        if jsonDict['locked']:
            retArray = [1, jsonDict['host'], jsonDict['comment']]
        else:
            retArray = [0, "", ""]

        self.__logging("getSlotLockInfo: retArray=%s" % (retArray))
        return retArray

    def getRackLockInfoFull(self, slotid):
        self.__logging("getRackLockInfoFull: %s" % (slotid))
        return self.getRackLockInfo(slotid)

    def getRackLockInfo(self, slotid):
        '''
        [[1, '-User-', '-Comment-', '1648014959', '00:00:08'], [0, '-User-', '-Comment-', '0', ''], ...]

        '''
        self.__logging("getRackLockInfo: %s" % (slotid))
        self.__loadSlotDetails(slotid)
        baseURL = self.__getBaseURL()
        u = "/v1/all/lock"
        url = "%s%s" % (baseURL, u)
        jsonStr = self.__getRequest(url)
        jsonDict = json.loads(jsonStr)
        # pprint(jsonDict)
        t = ti.time()
        rackArray = []
        for i in range(16):
            slotArray = []
            k = str(i + 1)
            slotInfo = jsonDict[k]
            if slotInfo['locked']:
                slotArray.append(1)
                slotArray.append(slotInfo['host'])
                slotArray.append(slotInfo['comment'])
                slotArray.append(str(slotInfo['lock_time']))
                tDiff = int(t) - int(slotInfo['lock_time'])
                s = self.__secs2hms(tDiff)
                slotArray.append(s)
            else:
                slotArray.append(0)
                slotArray.append("-User-")
                slotArray.append("-Comment-")
                slotArray.append("0")
                slotArray.append("")
            rackArray.append(slotArray)
        # self.__logging("getRackLockInfo: %s" % (pformat(rackArray)))
        return rackArray

    def killSlot(self, slotid):
        '''
        OK
        The specified slot is not locked
        '''
        self.__logging("killSlot: %s" % (slotid))
        self.__loadSlotDetails(slotid)
        baseURL = self.__getBaseURL()
        u = "/v1/admin/%s/force_unlock" % (self.__slotno)
        url = "%s%s" % (baseURL, u)

        forceUnlockJson = {
            "user": "SlotMonitor",
            "reason": "Somebody requested this"
        }
        jsonStr = self.__postRequest(url, json=forceUnlockJson)
        jsonDict = json.loads(jsonStr)
        s = pformat(jsonDict)
        self.__logging(s)
        retVal = None
        if jsonDict['unlocked']:
            retVal = "OK"

        return retVal

    def lockState(self, slotid):
        '''
            0 - Free
            1 - Locked
        '''
        self.__logging("lockState: %s" % (slotid))
        lockInfo = self.getSlotLockInfo(slotid)
        retVal = lockInfo[0]
        self.__logging("lockState: retVal=%s" % (retVal))
        return retVal

    def lockSlot(self, slotid, lockComment):
        self.__loadSlotDetails(slotid)

        sessionLock = self.sessionLockExists()
        if sessionLock:
            self.__logging("lockSlot: sessionLockExists", True)
            return False

        encodedComment = quote_plus(lockComment)
        baseURL = self.__getBaseURL()
        u = "/v1/%s/lock?expiry=36000&comment=%s" % (self.__slotno, encodedComment)
        url = "%s%s" % (baseURL, u)
        jsonStr = self.__putRequest(url)
        if jsonStr is None:
            return False
        jsonDict = json.loads(jsonStr)
        s = pformat(jsonDict)
        self.__logging(s)
        retVal = jsonDict['locked']
        self.__lockToken = jsonDict['token']
        return retVal

    def sessionLockExists(self):
        baseURL = self.__getRMbaseURL()
        u = "/v0/allocation/dut/%s" % (self.slotid)
        url = "%s%s" % (baseURL, u)
        self.__useProxies = True
        jsonStr = self.__getRequest(url)
        self.__useProxies = False
        if jsonStr is None:
            self.__logging("sessionLockExists FALSE")
            return False
        jsonDict = json.loads(jsonStr)
        s = pformat(jsonDict)
        self.__logging("sessionLockExists: %s" % (s))
        return True

    def unlockSlot(self, slotid):
        # self.__lockToken = "mql_3b6c62c3832b4f02f80d106a79feb5636ad0f7dfaf666272d51d70d804134de6.TeWmA7Bh22XXXz46bpYlgf5oUuY"
        self.__loadSlotDetails(slotid)
        baseURL = self.__getBaseURL()
        u = "/v1/%s/lock" % (self.__slotno)
        url = "%s%s" % (baseURL, u)
        jsonStr = self.__deleteRequest(url, self.__lockToken)
        if jsonStr is None:
            return True
        jsonDict = json.loads(jsonStr)
        s = pformat(jsonDict)
        self.__logging(s)
        retVal = jsonDict['unlocked']
        self.__lockToken = None
        return retVal

    def __getVideoLog(self, url, filename):
        from urllib.request import urlretrieve
        verbose = True
        try:
            if verbose:
                self.__logging("__getVideoLog: %s " % (url))
            dn = os.path.dirname(filename)
            if not os.path.exists(dn):
                os.makedirs(dn)
            urlretrieve(url, filename)
        except:
            filename = None
            tb = traceback.format_exc()
            self.__logging("__getVideoLog: %s " % (tb))

        if verbose:
            self.__logging("__getVideoLog: %s" % (filename))
        return filename

    def __getImage(self, url, filename):
        headers = {"Accept": "image/jpeg"}
        verbose = True
        img = None
        try:
            if verbose:
                self.__logging("getIMGdata: %s " % (url))
            r = requests.get(url, timeout=5, headers=headers)
            rc = r.status_code
            if int(rc) == 200:
                if verbose:
                    self.__logging("getIMGdata: %s OK" % (url))

                img = Image.open(BytesIO(r.content))
                dn = os.path.dirname(filename)
                if not os.path.exists(dn):
                    os.makedirs(dn)
                img.save(filename)
            else:
                self.__logging("getIMGdata: %s NOK status_code=%s" % (url, rc))
                filename = None
        except:
            filename = None
            tb = traceback.format_exc()
            self.__logging("getIMGdata: %s " % (tb))

        if verbose:
            self.__logging("getIMGdata: %s" % (filename))
        return filename

    def getCurrentScreenCapture(self):
        fn = self.getImage()
        im = Image.open(fn)
        return im, fn

    def __movieIcon(self, fn):
        dn = os.path.dirname(fn)
        movieJPG = os.path.join(dn, "movie.jpg")
        if os.path.exists(movieJPG):
            return movieJPG
        s64 = '''
        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
        '''
        s64bytes = base64.b64decode(s64.replace("\n", ""))
        fh = open(movieJPG, "wb")
        fh.write(s64bytes)
        fh.close()
        return movieJPG

    def __htmlImageLog(self, fn):
        unixFN = self.__getNASurl(fn)
        s = "<a target='_top' href='%s'><img title='HTML Captured Image' src='%s' height='10%%' border='0'></a>" % (
        unixFN, unixFN)
        print(s)

    def __htmlMovieLog(self, fn):
        movieJPG = self.__movieIcon(fn)
        movieIcon = self.__getNASurl(movieJPG)
        unixFN = self.__getNASurl(fn)
        s = "<a target='_top' href='%s'><img title='HTML Captured Video' src='%s' border='0'></a>" % (unixFN, movieIcon)
        print(s)

    def getVideoLog(self, pvrID, filename=None):
        if filename:
            split_tup = os.path.splitext(filename)
            if len(split_tup[1]) == 0:
                filename = "%s.mp4" % (filename)
        if not filename:
            nowSecsStr = "%s" % ti.time()
            nowSecsStr = nowSecsStr.replace(".", "_")
            vidName = "vid_%s.mp4" % (nowSecsStr)
            filename = os.path.join(self.logpath, vidName)
        baseURL = self.__getBaseURL()
        u = "/v1/%s/video/pvr/%s" % (self.__slotno, pvrID)
        url = "%s%s" % (baseURL, u)
        fn = self.__getVideoLog(url, filename)
        if fn:
            self.__htmlMovieLog(fn)
        return fn

    def getImage(self, filename=None):
        if filename:
            split_tup = os.path.splitext(filename)
            if len(split_tup[1]) == 0:
                filename = "%s.jpg" % (filename)
        if not filename:
            nowSecsStr = "%s" % ti.time()
            nowSecsStr = nowSecsStr.replace(".", "_")
            imageName = "img_%s.jpg" % (nowSecsStr)
            filename = os.path.join(self.logpath, imageName)
        baseURL = self.__getBaseURL()
        u = "/v1/%s/video/buffer/image" % (self.__slotno)
        url = "%s%s" % (baseURL, u)
        fn = self.__getImage(url, filename)
        return fn

    def listRemotes(self, slotid):
        self.__loadSlotDetails(slotid)
        baseURL = self.__getBaseURL()
        u = "/v1/%s/remotes" % (self.__slotno)
        url = "%s%s" % (baseURL, u)
        jsonStr = self.__getRequest(url)
        jsonDict = json.loads(jsonStr)
        # pprint(jsonDict)
        return jsonDict

    def listRemoteButtons(self, slotid, remoteName):
        self.__loadSlotDetails(slotid)
        baseURL = self.__getBaseURL()
        u = "/v1/%s/remote?remote=%s" % (self.__slotno, remoteName)
        url = "%s%s" % (baseURL, u)
        jsonStr = self.__getRequest(url)
        jsonDict = json.loads(jsonStr)
        # pprint(jsonDict)
        return jsonDict

    def __remapButtonEC202(self, keyname):
        newKeyName = keyname
        keyDict = {}
        keyDict['Home'] = "TV_Guide"
        keyDict['Ok'] = "Select"
        keyDict['Ch+'] = "Channel+"
        keyDict['Ch-'] = "Channel-"

        if keyname in list(keyDict.keys()):
            newKeyName = keyDict[keyname]

        return newKeyName

    def __remapButtonLC103(self, keyname):
        newKeyName = keyname
        keyDict = {}
        keyDict['Ok'] = "Ok"

        if keyname in list(keyDict.keys()):
            newKeyName = keyDict[keyname]

        return newKeyName

    def __remapButton(self, keyname, remoteName):
        if remoteName == "LC103":
            return self.__remapButtonLC103(keyname)
        return self.__remapButtonEC202(keyname)

    def pressButton(self, slotid, keyName, remoteName=None):
        self.__loadSlotDetails(slotid)
        baseURL = self.__getBaseURL()
        if remoteName is None:
            remoteName = self.redratFile
        if remoteName == "default":
            remoteName = None
        if remoteName:
            keyName = self.__remapButton(keyName, remoteName)
            encodedKeyName = quote_plus(keyName)
            u = "/v1/%s/remote?remote=%s&key=%s" % (self.__slotno, remoteName, encodedKeyName)
        else:
            encodedKeyName = quote_plus(keyName)
            u = "/v1/%s/remote?key=%s" % (self.__slotno, encodedKeyName)
        url = "%s%s" % (baseURL, u)
        jsonStr = self.__postRequest(url)
        jsonDict = None
        if jsonStr:
            jsonDict = json.loads(jsonStr)
        # pprint(jsonDict)
        return jsonDict

    def readOCR(self, region, lang=None):
        baseURL = self.__getBaseURL()
        x, y, w, h = region
        sRegion = "%s,%s,%s,%s" % (x, y, w, h)
        u = "/v1/analysis/ocr?lang=%s&region=%s" % (lang, sRegion)
        url = "%s%s" % (baseURL, u)
        fn = self.getImage()
        if fn is None:
            return None
        jsonStr = self.__ocrPostRequest(url, fn)
        if jsonStr is None:
            return None

        jsonDict = json.loads(jsonStr)
        '''
        {u'bbox': [514, 516, 548, 87],
         u'confidence': 75,
         u'ocr_text': u'-.-, -,.-. - -......- .... . Sky Sport Bunde 212 Sendepause'}
        '''
        cropArea = (x, y, x + w, y + h)
        self.__imageManager.markImage(fn, None, cropArea)
        self.__saveSTIO(fn)
        self.__imageManager.updateThumbnail(fn)
        s = pformat(jsonDict)
        self.__logging(s)
        return jsonDict

    def getSerialOutput(self):
        baseURL = self.__getBaseURL("ws")
        u = "/wsv1/%s/serial" % (self.__slotno)
        url = "%s%s" % (baseURL, u)

        maxTries = 3
        for i in range(maxTries):
            self.__logging("getSerialOutput: try %s" % (i))
            rawData = self.__wsGet(url, useLockToken=True)
            if rawData:
                break

        print()
        return rawData

    def audioDetection(self, threshold, timeoutAudioPresence):
        baseURL = self.__getBaseURL("ws")
        u = "/wsv1/%s/analysis/audio" % (self.__slotno)
        audioDict = {"threshold": threshold, "timeout": timeoutAudioPresence}
        dataStr = json.dumps(audioDict)
        url = "%s%s" % (baseURL, u)

        maxTries = 1
        for i in range(maxTries):
            self.__logging("audioDetection: try %s" % (i))
            jsonStr = self.__wsGet(url, dataStr)
            if jsonStr:
                break

        jsonDict = None
        if jsonStr:
            jsonDict = json.loads(jsonStr)
        return jsonDict

    def motionDetection(self, region, timeoutSec, percent):
        baseURL = self.__getBaseURL("ws")
        u = "/wsv1/%s/analysis/motion" % (self.__slotno)
        if region:
            motionDict = {"threshold": percent, "timeout": timeoutSec, "regions": "[%s]" % (region)}
        else:
            motionDict = {"threshold": percent, "timeout": timeoutSec}
        dataStr = json.dumps(motionDict)
        url = "%s%s" % (baseURL, u)

        maxTries = 1
        for i in range(maxTries):
            self.__logging("motionDetection: try %s" % (i))
            jsonStr = self.__wsGet(url, dataStr)
            if jsonStr:
                break
        jsonDict = None
        if jsonStr:
            jsonDict = json.loads(jsonStr)
        return jsonDict

    def setPower(self, power_status):
        '''
            on, off, reboot
        '''
        baseURL = self.__getBaseURL()
        u = "/v1/%s/power?power_status=%s" % (self.__slotno, power_status)
        url = "%s%s" % (baseURL, u)
        jsonStr = self.__putRequest(url)
        if jsonStr is None:
            return None
        jsonDict = json.loads(jsonStr)
        s = pformat(jsonDict)
        self.__logging(s)
        return jsonDict

    def getPower(self, allSlots=False):
        baseURL = self.__getBaseURL()
        if allSlots:
            u = "/v1/all/power"
        else:
            u = "/v1/%s/power" % (self.__slotno)
        url = "%s%s" % (baseURL, u)
        jsonStr = self.__getRequest(url)
        if jsonStr is None:
            return None
        jsonDict = json.loads(jsonStr)
        # pprint(jsonDict)
        return jsonDict

    def listStreams(self):
        baseURL = self.__getBaseURL()
        u = "/v1/%s/video/stream" % (self.__slotno)
        url = "%s%s" % (baseURL, u)
        jsonStr = self.__getRequest(url)
        if jsonStr is None:
            return None
        jsonDict = json.loads(jsonStr)
        s = pformat(jsonDict)
        self.__logging(s)
        return jsonDict

    def setStreamParams(self, bitRate):
        streamParams_high = {
            "res_w": 1920,
            "res_h": 1080,
            "force_sw_enc": True,
            "crf": 3,
            "fps": 25,
            "max_bitrate": bitRate
        }
        streamParams_low = {
            "res_w": 768,
            "crf": 31,
            "res_h": 432,
            "fps": 25,
            "max_bitrate": bitRate
        }
        streamParams = streamParams_high
        if int(bitRate) < 1000000:
            # Just use the standard stream - default = 0
            streamParams = streamParams_low
            return "OK"

        baseURL = self.__getBaseURL()
        u = "/v1/%s/video/stream?force=true" % (self.__slotno)
        url = "%s%s" % (baseURL, u)
        jsonStr = self.__postRequest(url, json=streamParams)
        jsonDict = json.loads(jsonStr)
        s = pformat(jsonDict)
        self.__logging(s)
        retVal = None
        if jsonDict['id']:
            self.__streamID = jsonDict['id']
            retVal = "OK"

        return retVal

    def startVideoLog(self):
        baseURL = self.__getBaseURL()
        if self.__streamID:
            u = "/v1/%s/video/pvr?stream_id=%s" % (self.__slotno, self.__streamID)
        else:
            u = "/v1/%s/video/pvr" % (self.__slotno)

        url = "%s%s" % (baseURL, u)
        jsonStr = self.__postRequest(url)
        if jsonStr is None:
            return None
        jsonDict = json.loads(jsonStr)
        # self.listStreams()
        return jsonDict

    def stopVideoLog(self, pvrID):
        baseURL = self.__getBaseURL()
        u = "/v1/%s/video/pvr/%s/stop" % (self.__slotno, pvrID)
        url = "%s%s" % (baseURL, u)
        jsonStr = self.__postRequest(url)
        if jsonStr is None:
            return None
        jsonDict = json.loads(jsonStr)

        if self.__streamID:
            u = "/v1/%s/video/stream?stream_id=%s" % (self.__slotno, self.__streamID)
            url = "%s%s" % (baseURL, u)
            s = self.__deleteRequest(url, self.__lockToken)
            self.__logging("remove_stream: %s" % (s))

        # pprint(jsonDict)
        return jsonDict

    def listRecordings(self, slotid):
        self.__logging("listRecordings: %s" % (slotid))
        self.__loadSlotDetails(slotid)
        baseURL = self.__getBaseURL()
        u = "/v1/%s/video/pvr" % (self.__slotno)
        url = "%s%s" % (baseURL, u)
        jsonStr = self.__getRequest(url)
        if jsonStr is None:
            return None
        jsonDict = json.loads(jsonStr)
        # pprint(jsonDict)
        return jsonDict

    def videoInfo(self, allSlots=False):
        baseURL = self.__getBaseURL()
        if allSlots:
            u = "/v1/all/video/buffer"
        else:
            u = "/v1/%s/video/buffer" % (self.__slotno)
        url = "%s%s" % (baseURL, u)
        jsonStr = self.__getRequest(url)
        if jsonStr is None:
            return None
        jsonDict = json.loads(jsonStr)
        # pprint(jsonDict)
        return jsonDict

    def startHighSpeedCapture(self, highSpeedDict):
        '''
        self.__highSpeedInfoDict['maxFrames'] = maxFrames
        self.__highSpeedInfoDict['startFrame'] = startFrame
        self.__highSpeedInfoDict['skipCount'] = skipCount
        self.__highSpeedInfoDict['trigger'] = irKey
        self.__highSpeedInfoDict['trigger_count'] = keyCount
        self.__highSpeedInfoDict['timeout'] = timeout

        '''
        k = "trigger"
        if k in highSpeedDict:
            irKey = self.__remapButton(highSpeedDict[k], self.redratFile)
            highSpeedDict[k] = irKey

        if highSpeedDict[k]:
            highSpeedDict[k] = quote_plus(highSpeedDict[k])

        u = "/v1/%s/video/reserved?start_frame=%s" % (self.__slotno, highSpeedDict['startFrame'])
        u = "%s&max_frames=%s" % (u, highSpeedDict['maxFrames'])
        u = "%s&skip_frames=%s" % (u, highSpeedDict['skipCount'])
        u = "%s&trigger=%s" % (u, highSpeedDict['trigger'])
        u = "%s&trigger_count=%s" % (u, highSpeedDict['trigger_count'])
        baseURL = self.__getBaseURL()
        url = "%s%s" % (baseURL, u)
        jsonStr = self.__putRequest(url)
        jsonDict = json.loads(jsonStr)
        return jsonDict

    def getHighSpeedInfo(self):
        u = "/v1/%s/video/reserved" % (self.__slotno)
        baseURL = self.__getBaseURL()
        url = "%s%s" % (baseURL, u)
        jsonStr = self.__getRequest(url)
        jsonDict = json.loads(jsonStr)
        return jsonDict

    def stopHighSpeedCapture(self):
        u = "/v1/%s/video/reserved" % (self.__slotno)
        baseURL = self.__getBaseURL()
        url = "%s%s" % (baseURL, u)
        jsonStr = self.__deleteRequest(url, self.__lockToken)
        jsonDict = json.loads(jsonStr)
        return jsonDict

    def getHighSpeedFrame(self, idx):
        u = "/v1/%s/video/reserved/image?frame=%s" % (self.__slotno, idx)
        baseURL = self.__getBaseURL()
        url = "%s%s" % (baseURL, u)
        imageName = "frame_%.3d.jpg" % (idx)
        filename = os.path.join(self.logpath, imageName)
        fn = self.__getImage(url, filename)
        if fn:
            self.__htmlImageLog(fn)
        return fn

    def getVersion(self):
        u = "/v1/version"
        baseURL = self.__getBaseURL()
        url = "%s%s" % (baseURL, u)
        jsonStr = self.__getRequest(url)
        jsonDict = json.loads(jsonStr)
        v = jsonDict['main']
        return v


def Main():
    #
    # Alwqys lock the slot first!
    #
    slotid = 81509
    webAPI = MagiqWebAPI()
    webAPI.logpath = "."

    lockSlot = webAPI.lockSlot(slotid, "dsdsds")
    print("lockSlot - ", lockSlot)

    fn = webAPI.getCurrentScreenCapture()
    print('get screenshot {}'.format(fn))
    # lockState = webAPI.lockState(slotid)
    # print "lockState - ", lockState
    # slotLockInfo = webAPI.getSlotLockInfo(slotid)
    # print "slotLockInfo - ", slotLockInfo
    # rackLockInfo = webAPI.getRackLockInfo(slotid)
    # print rackLockInfo
    # killResult = webAPI.killSlot(slotid)
    # print killResult
    # dd = webAPI.getVersion()
    # print dd

    # dd = webAPI.sessionLockExists()
    # print "sessionLockExists - ", dd

    # d = webAPI.getSerialOutput()
    # print d

    # listRemotes = webAPI.listRemotes(slotid)
    # pprint(listRemotes)
    # listRemoteButtons = webAPI.listRemoteButtons(slotid, "LC103")
    # print(listRemoteButtons)

    # pvrID = "1de9b91b-1294-419e-98f3-e6752531bda9"
    # ret = webAPI.stopVideoLog(pvrID)
    # pprint(ret)
    # listRecordings = webAPI.listRecordings(slotid)
    # pprint(listRecordings)

    # ret = webAPI.getVideoLog(pvrID)
    # pprint(ret)

    unlockSlot = webAPI.unlockSlot(slotid)
    print(unlockSlot)


if __name__ == '__main__':
    Main()
    print("Done")
