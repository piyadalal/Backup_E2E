import traceback
import time
import socket
import os
import re
import json
#from ethanSTBdb import getSlot_ID
from pprint import pprint, pformat


class EthanStormtestClient():

    def __init__(self):
        self.__allScreensList = []
        self.__api = None
        self.slotNo = None
        self.configServer = "tech-hv16-1"
        self.serverIP = None
        self.redratFile = "default"
        self.connected = False
        # When developing or running unit tests set to false
        self.useStormtest = True
        self.useMagiq = False
        self.testResult = None
        self.navigatorName = None
        self.navigatorPath = None
        self.navigatorScreenList = None
        self.navigatorFolder = None
        self.frameworkFolder = None
        self.logPath = None
        self.slotInfoDict = None
        self.isServerRun = None
        self.soakroomSever = False
        self.host = None
        self.hdServer = False
        self.__saveScreenRegions = True
        self.hasSubslots = False
        self.currentSubslot = 0
        self.modelType = None
        self.videoLogRunning = False
        self.keysPressed = []
        self.NASip = None
        self.createTestSteps = True
        self.stIF = None
        self.resultID = None
        self.scriptPath = None
        self.epgVersion = None
        self.__screenComparer = None
        self.__imageManager = None
        self.slot_id = -1
        self.showWindow = 0
        self.__tocrClient = None
        self.__useTesseract = False
        self.objReporter = None
        self.imagePath = None
        self.__videoParams = None

    def screenshotAndResize(self, rect, f, imageQuality, inputArea=[0, 0, 1920, 1080], outputArea=[64, 34, 1920, 1080]):
        '''
        We call stio.Save() twice, once in CaptureImageEx and again with im_transformed.Save()
        Therefore we get two thumbnail images in the logfile.
        The thumbnails will differ, since 1st one is the real image and 2nd one the transformed image.
        But they both point to the same transformed image.

        Alternatively use2thumbnails = False.
        Then we get just one thumbnail image and it is of the first image.

        updateThumbnail will correct the thumbnail image

        screenshot 80101 resolution: 0; 0; 1920; 1080
        squeezed to: best match: 0; 0; 1854; 1044
        0; 0; 1855; 1045
        or 0; 0; 1856; 1046

        '''
        print("screenshotAndResize start")
        converter = self.__api.GetWorldToDesignTransform()[0][1]
        converter.SetFromRectangles(inputArea, outputArea)

        res = self.__captureImageEx(rect, f, imageQuality)
        __, rc, image, saved_fn = res[0]

        im_transformed = image.Transform(converter)
        image.Close()
        os.unlink(saved_fn)

        use2thumbnails = False
        if use2thumbnails:
            im_transformed.Save(saved_fn)
            last_fn = im_transformed.GetLastSavedName()
            print("screenshotAndResize: CaptureImageEx=%s GetLastSavedName=%s" % (os.path.basename(saved_fn), os.path.basename(last_fn)))
        else:
            pilImage = im_transformed.ToPILImage(retainRawImage=True)
            pilImage.save(saved_fn)
            last_fn = saved_fn
            print("screenshotAndResize: CaptureImageEx=%s pilImage.save=%s" % (os.path.basename(saved_fn), os.path.basename(last_fn)))

        self.__imageManager.updateThumbnail(last_fn)
        slotArray = [self.slotNo, rc, im_transformed, last_fn]
        retArray = [slotArray]
        print("screenshotAndResize end")
        return retArray

    def checkSlots(self):
        ret = self.__api.CheckSlots()
        return ret

    def getReservedStatus(self):
        ret = self.__api.GetReservedStatus(self.configServer, self.slotNo)
        # pprint(ret)
        state = ret[0]['Reserved']
        return state

    def createScreenDefinition(self, refImagePath, rect, treshold, screenSize=(704, 576)):
        '''
        Create SDO object with only one Image comparison region!

        IN:
            refImagePath - path to the image to be inserted to only region area defined by rect param
            rect = eg. rectangular value from Navigator (119, 54, 203, 54)
            treshold = e.g shall be in most cases enough 80
            screenSize  =(704,576) standard screen size for SD video
        OUT:
            sdo - object with one region defined and one ref image object within that region
            sdoFilePath - saves sdo to the file path
        '''

        sdo = self.__api.ScreenDefinition()
        sdo.DesignSize = screenSize
        region = self.__api.ImageRegion('DefaultImageRegion', treshold, rect)
        region.SetImage(refImagePath)
        sdo.Regions.append(region)

        # extract file name from path
        refImageNameExtension = os.path.basename(refImagePath)  # or head, tail = os.path.split("/tmp/d/a.dat") print(tail) a.dat

        sdo.Name = os.path.splitext(refImageNameExtension)[0]
        sdoFilePath = self.__api.GetLogFileDirectory() + os.sep + str(sdo.Name) + ".stscreen"
        sdo.Save(sdoFilePath)

        return sdo, sdoFilePath

    def getLogPath(self):
        return self.logPath

    def getCurrentSubslot(self):
        return self.currentSubslot

    def set_subslot(self, subslot):
        if ((subslot < 0) or (subslot > 4)):
            print(("EthanStormtestClient.set_subslot: subslot parameter is not in range 0-4 %s" % (subslot)))
            raise Exception('subslot parameter is not in range 0-4')

        if self.currentSubslot == subslot:
            return True

        ret = self.__api.SetCurrentSubslot(subslot, self.slotNo)
        if ret == 1:
            self.currentSubslot = subslot
            self.__api.WaitSec(2)  # Video Switch
        else:
            print(("EthanStormtestClient.set_subslot: failed to set subslot %s" % (subslot)))
            return False

        return True

    def setSaveScreenRegions(self, b):
        self.__saveScreenRegions = b
        print("StormtestClient: setSaveRegions=%s" % (b))

    '''
    PASS         = 111
    PARTIAL_PASS = 110
    FAIL         = 100
    NOT_RUN      = 101
    '''

    def getTestResultString(self, r):
        self.__set_api()
        if r == self.__api.TM.NOT_RUN:
            return "NOT_RUN"
        if r == self.__api.TM.PASS:
            return "PASS"
        if r == self.__api.TM.PARTIAL_PASS:
            return "PARTIAL_PASS"
        if r == self.__api.TM.FAIL:
            return "FAIL"

    def getTestResult(self, result):
        self.__set_api()
        if isinstance(result, bool):
            if result:
                r = self.__api.TM.PASS
            else:
                r = self.__api.TM.FAIL
            return r

        if result is None:
            r = self.__api.TM.FAIL
            return r

        r = self.__api.TM.FAIL

        if result.lower() == "pass":
            r = self.__api.TM.PASS
        if result.lower() == "fail":
            r = self.__api.TM.FAIL
        if result.lower() == "partial_pass":
            r = self.__api.TM.PARTIAL_PASS
        if result.lower() == "not_run":
            r = self.__api.TM.NOT_RUN
        return r

    def setTestResult(self, result):
        r = self.getTestResult(result)
        self.testResult = r

    def is_serverRun(self):
        if self.isServerRun is not None:
            return self.isServerRun

        self.host = socket.gethostname()
        print(self.host)
        rc = False
        if self.host == "tech-hs64-1":
            rc = True
            self.soakroomSever = True
        if self.host == "tech-hs64-2":
            rc = True
            self.soakroomSever = True
        if self.host == "tech-hv16-1":
            rc = True
            self.soakroomSever = True
        if self.host == "TPS-HS64-1":
            rc = True
            self.soakroomSever = True
        if self.host == "WIN10-SOAKROOM":
            rc = True
            self.soakroomSever = False
        if self.host == "tamuc06":
            rc = True
            self.soakroomSever = False
            from stormtestIF import StormtestIF  # @UnresolvedImport
            self.stIF = StormtestIF()

        print("is_serverRun: hostName=%s rc=%s" % (self.host, rc))
        self.isServerRun = rc
        return rc

    def showVideo(self, ignoreServerRun=False):
        # monitoring video for client only
        showVideoWindow = True
        if ignoreServerRun:
            showVideoWindow = True
        else:
            rc = self.is_serverRun()
            if rc:
                showVideoWindow = False
            else:
                if self.showWindow == 0:
                    showVideoWindow = False
        print("showVideo: showVideoWindow=%s " % (showVideoWindow))
        if showVideoWindow:
            self.__api.ShowVideo(slotNo=self.slotNo)

    def closeVideo(self):
        # monitoring video for client only
        print("closeVideo")
        rc = self.is_serverRun()
        if not rc:
            self.__api.CloseVideo(self.slotNo)

    def doOCRconfig(self, forceTesseract=False):
        if self.useMagiq and not forceTesseract:
            self.__tocrClient = None
            self.__useTesseract = False
            return

        from ocr_tesseract_client import TesseractOCRclient
        self.__tocrClient = TesseractOCRclient(self.slot_id)
        self.__useTesseract = self.__tocrClient.useTesseract

    def __set_api_stormtest(self):
        if self.__api is None:
            import stormtest.ClientAPI as ClientAPI  # @UnresolvedImport
            self.__api = ClientAPI

    def __set_api_magiq(self):
        if self.__api is None:
            from magiqClientAPI import MagiqClientAPI  # @UnresolvedImport
            self.__api = MagiqClientAPI()
            self.__api.loadApi()
            self.__saveScreenRegions = False
            self.redratFile = self.modelType.RCU()

    def __set_api(self):
        from imageManager import ImageManager  # @UnresolvedImport
        self.__imageManager = ImageManager()
        if self.useMagiq:
            self.__set_api_magiq()
        else:
            self.__set_api_stormtest()

    def setStormtestAPI(self):
        self.__set_api_stormtest()

    def getSlotID(self):
        rc = self.is_serverRun()
        if not rc:
            return False
        try:
            self.__set_api()
            print("getSlotID: SetMasterConfigurationServer %s" % (self.serverIP))
            self.__api.SetMasterConfigurationServer(self.serverIP)
        except:
            traceback.print_exc()
            return False

        ret = self.__api.GetPhysicalAllocations()
        hostNamePort = ret[0]
        serverIP = hostNamePort[:hostNamePort.find(':')]
        allocatedSlots = ret[1]
        slot = allocatedSlots[0]
        slotID = getSlot_ID(serverIP, slot)
        print("getSlot_ID: serverIP=%s slot=%s slotID=%s" % (serverIP, slot, slotID))
        return slotID

    def connect(self, slot, server, serverIP=None):
        # connect to stormtest
        self.slotNo = slot


        self.serverIP = server
        if serverIP:
            self.serverIP = serverIP

        if "tech" not in server:
            self.configServer = server
            print(self.configServer)

        if self.configServer.lower().startswith("stormtest8"):
            self.hdServer = True
            self.createTestSteps = False

        if self.configServer.lower().startswith("magiq"):
            self.hdServer = True
            self.createTestSteps = False
            self.useMagiq = True

        if self.__api is None:
            try:
                self.__set_api()
                print("SetMasterConfigurationServer %s" % (self.serverIP))
                self.__api.SetMasterConfigurationServer(self.serverIP)
            except:
                traceback.print_exc()
                return False

        self.testResult = self.__api.TM.NOT_RUN
        if self.logPath is None:
            if not self.is_serverRun():
                self.__api.SetDirectories(logDir="log")
        else:
            self.__api.SetProjectDir(self.logPath)

        self.logPath = self.__api.GetLogFileDirectory()

        print("Connecting to server=%s slot=%s redrat_file=%s logPath=%s" % (self.serverIP, self.slotNo, self.redratFile, self.logPath))
        if self.stIF and self.resultID:
            self.stIF.correctLogpath(self.resultID, self.logPath)

        if not self.useStormtest:
            self.connected = True
            return self.connected

        try:
            connectStr = ""
            bn = "unknown"
            if self.scriptPath:
                bn = os.path.basename(self.scriptPath)
            if self.resultID:
                connectStr = "%s_%s" % (self.resultID, bn)
            else:
                connectStr = "%s_%s" % (self.host, bn)
            if self.useMagiq:
                ret = self.__api.ConnectToServer(self.configServer, connectStr)
            else:
                ret = self.__api.ConnectToServer(self.serverIP, connectStr)
            if not ret:
                return False
            serialParams = [115200, 8, "none", 1, "none"]
            ret = self.__api.ReserveSlot(
                self.slotNo, self.redratFile, serialParams,videoFlag=True)
            if ret == 1:
                pass
            else:
                print("INFO: Slot %s %s is unavailable" % (self.serverIP, self.slotNo))
                return False
            if not self.isServerRun:
                self.showVideo()
        except:
            traceback.print_exc()
            return False

        self.setNavigatorFolder()
        self.connected = True
        if not self.hdServer:
            self.getSlotInfo()
        if self.hasSubslots:
            self.currentSubslot = self.__api.GetCurrentSubslot(self.slotNo)
        return self.connected

    def release(self):
        if not self.connected:
            print("EthanStormtestClient() release: Not connected")
            return True
        # connect to srormtest
        print("Releasing slot=%s" % (self.slotNo))
        if self.useStormtest:
            print("Final Test Result = %s" % (self.getTestResultString(self.testResult)))
            self.stopVideoLogRecording()
            self.closeVideo()
            self.closeNavigator()
            self.__api.FreeSlot(self.slotNo)
            self.__api.ReleaseServerConnection()
            if not self.hdServer:
                rc = self.is_serverRun()
                if rc:
                    self.__api.ReturnTestResult(self.testResult)
        self.slotNo = None
        self.connected = False
        return True

    def waitSecs(self, secs):
        waitMilliSecs = secs * 1000
        self.waitMilliSecs(waitMilliSecs)

    def waitMilliSecs(self, waitMilliSecs):
        if isinstance(waitMilliSecs, str):
            waitMilliSecs = int(waitMilliSecs)
        if waitMilliSecs > 0:
            sec = float(waitMilliSecs) / 1000
            # print "EthanStormtestClient: Waiting...%s" % (sec)
            self.__api.WaitSec(sec)

    def remapKeyEthanSatAmidala(self, key):
        newKey = key

        keyDict = {}
        keyDict['Ok'] = "Select"
        keyDict['Back'] = "Backup"
        keyDict['Sky'] = "SKY"

        if self.useMagiq:
            keyDict['Search'] = "Services"
            keyDict['Apps'] = "Interactive"

        if key in list(keyDict.keys()):
            newKey = keyDict[key]

        return newKey

    def remapKeyAmidalaEthanSat(self, key):
        newKey = key

        keyDict = {}
        keyDict['Select'] = "Ok"
        keyDict['Backup'] = "Back"
        keyDict['SKY'] = "Sky"

        if key in list(keyDict.keys()):
            newKey = keyDict[key]

        return newKey

    def remapKeyXiOne(self, key):
        newKey = key

        '''
        Add the standard definition -> EC202 definition
        '''
        keyDict = {}
        keyDict['Home'] = "TV_Guide"
        keyDict['Back'] = "Backup"
        keyDict['Ok'] = "Select"
        keyDict['Search'] = "Services"
        keyDict['Apps'] = "Interactive"
        keyDict['Sky'] = "SKY"
        keyDict['Play/Pause'] = "Play"

        if key in list(keyDict.keys()):
            newKey = keyDict[key]

        return newKey

    def remapKeyX3(self, key):
        newKey = key

        '''
        Add the standard definition -> LC103 definition
        '''
        keyDict = {}
        # Old to New IR command mapping
        keyDict['Back'] = "Backup"
        keyDict['Sky'] = "Home"
        keyDict['Select'] = "Ok"

        if key in list(keyDict.keys()):
            newKey = keyDict[key]

        return newKey

    def remapKey(self, key):
        model = self.slotInfoDict['Model']
        if model == "Amidala":
            key = self.remapKeyEthanSatAmidala(key)
        if model == "Ethan":
            key = self.remapKeyAmidalaEthanSat(key)
        if model == "Jupiter":
            key = self.remapKeyAmidalaEthanSat(key)
        if model == "Hamburg":
            key = self.remapKeyAmidalaEthanSat(key)
        if model == "XiOne":
            key = self.remapKeyXiOne(key)
        if model == "Mozart":
            key = self.remapKeyEthanSatAmidala(key)
        if model == "QMS":
            key = self.remapKeyEthanSatAmidala(key)
        if model == "Alpaca" or model == "X3" or model == "Llama":
            key = self.remapKeyX3(key)

        return key

    def pressButton(self, key, waitMilliSecs=0):
        model = self.slotInfoDict['Model']
        if not self.connected:
            print("EthanStormtestClient() pressButton: Not connected")
            return False
        ret = -2
        # print "EthanStormtestClient.pressButton() button=%s" % (key)

        key = str(key)
        if self.useStormtest:
            if key.isdigit():
                keyLen = len(key)
                if self.host == "tamuc06" and keyLen > 1:
                    for i in range(keyLen):
                        ret = self.__api.PressButton(key[i])
                        if i < (keyLen - 1):
                            self.waitMilliSecs(700)
                else:
                    for i in range(keyLen):
                        ret = self.__api.PressButton(key[i])
                        if keyLen > 1 and i < (keyLen - 1):
                            self.waitMilliSecs(500)
            else:
                key = self.remapKey(key)
                ret = self.__api.PressButton(key)
        s = "%s/%.1fs" % (key, float(waitMilliSecs) / 1000)
        self.keysPressed.append(s)
        if self.objReporter:
            if self.stormtestClient.objReporter != None:
                self.objReporter.objTestHeartBeats.updateIR(s)
        if isinstance(waitMilliSecs, str):
            waitMilliSecs = int(waitMilliSecs)
        if waitMilliSecs > 0:
            self.waitMilliSecs(waitMilliSecs)

        if not self.useStormtest:
            ret = 1

        print("EthanStormtestClient() model=%s pressButton=%s ret=%s" % (model, key, ret))
        if ret == 1:
            return True

        return False

    def writeKeysPressed(self, imageFile):
        if len(self.keysPressed) == 0:
            return

        txtPath = None
        if imageFile is None:
            imageFile = "None"
        if imageFile.endswith(".jpg"):
            txtPath = imageFile.replace(".jpg", ".txt")
        if imageFile.endswith(".png"):
            txtPath = imageFile.replace(".png", ".txt")
        if txtPath is None:
            print("ERROR: unknown image type [%s]" % (imageFile))
            return

        with open(txtPath, 'w') as f:
            for item in self.keysPressed:
                f.write("%s\n" % item)

        self.keysPressed = []

    def saveSTIO(self, stio, imagePath):
        pilImage = stio.ToPILImage()
        pilImage.save(imagePath)
        return True

    def saveScreen(self, logstr=None, testStep=False, stepResult=True):
        self.imagePath = None
        nowSecsStr = "%s" % time.time()
        nowSecsStr = nowSecsStr.replace(".", "_")
        if self.hasSubslots:
            imageName = "img_%s_sub_%s.jpg" % (nowSecsStr, self.currentSubslot)
        else:
            imageName = "img_%s.jpg" % (nowSecsStr)

        if testStep:
            if stepResult:
                imageName = imageName.replace(".jpg", "P.jpg")
            else:
                imageName = imageName.replace(".jpg", "F.jpg")

        ret = self.captureImageEx(None, imageName)
        imagePath = ret[0][3]
        rc = ret[0][1]
        print("saveScreen: %s returned=%s" % (imagePath, rc))
        if imagePath is None:
            return None

        self.writeKeysPressed(imagePath)

        if logstr is not None and rc:
            stio = ret[0][2]
            stio.Close()
            from PIL import ImageDraw, ImageFont, Image
            pilImage = Image.open(imagePath)
            font = ImageFont.load_default()
            draw = ImageDraw.Draw(pilImage)
            commentLen = 200
            commentStr = (logstr[:commentLen] + '..') if len(logstr) > commentLen else logstr
            imageComment = "Sub:%s %s" % (self.currentSubslot, commentStr)
            imageComment = imageComment.encode("latin-1", "replace")
            draw.text((0, 0), imageComment, font=font, fill="yellow")
            pilImage.save(imagePath)
            del pilImage
            del font
            del draw

        ret[0][2].Close()

        if rc:
            self.imagePath = imagePath
            return imagePath
        else:
            return None

    def saveScreenRegion(self, regionName, regionRect=None):
        if not self.__saveScreenRegions:
            print("saveScreenRegion(): deactivated")
            return None

        if regionName is not None:
            region = self.__api.FindNamedRegion(regionName)
            imageRegionName = regionName.replace("/", "_")
        else:
            region = regionRect
            imageRegionName = "regionRect"

        nowSecsStr = "%s" % time.time()
        nowSecsStr = nowSecsStr.replace(".", "_")
        if self.hasSubslots:
            imageName = "region_img_%s_%s_sub_%s.jpg" % (nowSecsStr, imageRegionName, self.currentSubslot)
        else:
            imageName = "region_img_%s_%s.jpg" % (nowSecsStr, imageRegionName)

        ret = self.captureImageEx(region, imageName)
        imagePath = ret[0][3]
        rc = ret[0][1]
        ret[0][2].Close()
        print("saveScreenRegion: %s returned=%s" % (imagePath, rc))
        if rc:
            return imagePath
        else:
            return None

    def is_audio(self, thMin=-45.0, thMax=-10.0):
        """
        thMin/Max - min and max threshold. All audio values in between return True
                    otherwise False.
        """
        # WaitAudioPresence(Int32 slotNo, Double threshold, Double timeout)
        timeoutAudioPresence = 5
        # dBu
        threshold = thMin
        print("is_audio: thMin=%s thMax=%s timeoutAudioPresence=%s " % (thMin, thMax, timeoutAudioPresence))
        status = self.__api.WaitAudioPresence(
            threshold, timeoutAudioPresence, self.slotNo)

        if status[1] > thMax:
            print("is_audio: > thMax %s" % (thMax))
            status[0] = False

        print("is_audio: returned=%s" % (status))
        return status[0]

    def is_motion(self, namedRegion=None, percent=5):
        # ret = DetectMotionEx((600,0,104,75),5,percent=5,slotNo = 8)
        timeoutSec = 5
        status = self.__api.DetectMotionEx(namedRegion, timeoutSec, percent, self.slotNo)
        s = pformat(status)
        print("is_motion: returned=%s" % (s))
        if isinstance(status[2], self.__api.Imaging.StormTestImageObject):
            status[2].Close()
            del status[2]
        return status[1]

    def getSlotInfo(self):
        if self.slotInfoDict is None:
            rawData = self.__api.GetFacilityData(self.serverIP)
            allFieldsSlot = self.__api.GetStbField(
                rawData, self.serverIP, self.slotNo, "all")  # get
            print("getSlotInfo: %s" % (allFieldsSlot))
            self.slotInfoDict = allFieldsSlot
            if self.getSlotID():
                dutSmartcardList = json.loads(self.slotInfoDict['SmartCardNumber'])
                nSmartCards = len(dutSmartcardList)
                if nSmartCards == 1:
                    self.hasSubslots = False
                else:
                    self.hasSubslots = True

        return self.slotInfoDict

    def stormtestCreateTestStep(self, step, comment, result):
        r = self.getTestResult(result)

        sStep = str(step)

        if self.currentSubslot > 0:
            sStep = "{}_sub_{}".format(sStep, self.currentSubslot)

        ret = True
        print("TestStep: {} | {} | {}".format(sStep, result, comment))
        # {} should not be used in Steps.
        # {} are allowed in comments
        sStep = sStep.replace("{", "[")
        sStep = sStep.replace("}", "]")
        if self.is_serverRun() and sStep != "":
            if self.stIF:
                if self.resultID:
                    self.stIF.addTestStep(self.resultID, sStep, comment, r)
                return

            if self.createTestSteps:
                ret = self.__api.BeginTestStep(sStep)
                if ret:
                    ret = self.__api.EndTestStep(sStep, r, comment)
        return ret

    def closeNavigator(self):
        if self.navigatorPath is None:
            return
        print("closeNavigator")
        res = self.__api.CloseNavigator(self.slotNo)
        if not res:
            print("Warning: closeNavigator() failed")
        self.navigatorPath = None

    def setNavigatorFolder(self):
        working_dir = str(os.path.dirname(__file__))
        rc = self.is_serverRun()
        if rc:
            referenceDir = "public"
            if referenceDir not in working_dir:
                referenceDir = "automated_tests"
            if "public\\DEBUG" in working_dir:
                referenceDir = "public\\DEBUG"

        else:
            referenceDir = "automated_tests"
        startIndex = working_dir.find(referenceDir)
        pathBase = working_dir[:startIndex + len(referenceDir)]
        self.navigatorFolder = os.path.join(pathBase,
                                            "framework",
                                            "navigators")

        self.frameworkFolder = os.path.join(pathBase,
                                            "framework")

        print("setNavigatorFolder: %s" % (self.navigatorFolder))

    def openNavigator(self, navigator=None):
        if navigator is None:
            navigator = self.getModelTypeNavigator()

        navigatorFile = "%s.stnav_runtime" % (navigator)
        navigatorFilepath = os.path.join(self.navigatorFolder,
                                         navigatorFile)

        if self.navigatorPath == navigatorFilepath:
            return True
        self.closeNavigator()

        res = self.__api.OpenNavigatorFile(navigatorFilepath, self.slotNo)
        if not res:
            print("Warning: OpenNavigatorFile() %s failed" % (navigatorFilepath))
            return False
        print("openNavigator: %s" % (navigatorFilepath))
        self.navigatorPath = navigatorFilepath
        self.navigatorScreenList = self.__api.GetNavigatorScreens(self.slotNo)
        self.navigatorName = navigator
        return True

    def getAllScreens(self, navigatorName, screenToValidate):
        # get all screen version of screen screenToValidate in currently selected navigator
        # navigator has to be opened already
        # all screen version of screen screenToValidate are of format:
        # screenToValidate + _verXY
        # where XY is any integer

        # screenList consist of all screens connected and not connected
        screenList = self.getScreenList(navigatorName)

        if screenToValidate is None:
            return []

        # select screens for navigation list
        validateScreenList = []
        for screen in screenList:
            if screenToValidate in screen:
                # check if we found target screen or its duplicate
                if screenToValidate == screen:
                    # 100% match
                    validateScreenList.append(screen)
                if screenToValidate + "_ver" in screen:
                    # if not 100% screen name match check if there are duplicates available
                    # duplicates screens are of following format:
                    # screenToValidate + _verXY
                    # where XY is any integer
                    verIndex = screen.lower().rfind("_ver")
                    if verIndex > -1:
                        # found candidate for duplicate screen lets check if false alarm
                        # positive candidates are those who have only number after _ver
                        numberCheck = screen[verIndex + len("_ver"):]
                        if numberCheck.isdigit():
                            # here we are sure that we found duplicate screen

                            # check if screen does not have any prefix making it bad match
                            if screen.find(screenToValidate) == 0:
                                validateScreenList.append(screen)

        validateScreenList.sort()
        # print "List of all screen to test against: " + str(validateScreenList)

        # temporary introduced after migration
        screenFile = self.getLogPath() + os.sep + "screens_in_use.txt"  # old stormtestClient.GetLogFileDirectory()
        fobjWrite = open(screenFile, 'a')

        # write to file only new screens
        for screen in validateScreenList:
            if screen not in self.__allScreensList:
                fobjWrite.write(screen + "\n")
                self.__allScreensList.append(screen)

        fobjWrite.close()

        return validateScreenList

    def logReferenceScreenRegions(self, screen, rName):
        if not self.__saveScreenRegions:
            print("logReferenceScreenRegions(): deactivated")
            return None

        regionDict = self.getScreenRegionDict(screen)
        sdo = regionDict[rName]['sdo']
        rect = sdo.Rect

        print("Actual region image %s.%s" % (screen, rName))
        # Save the current image region
        self.saveScreenRegion(regionName=None, regionRect=rect)

        print("Reference region image %s.%s" % (screen, rName))
        # Save the current image region again
        # Overwrite the current image with the reference image
        image = sdo.ReferenceImage
        pilImage = image.ToPILImage()
        refImagePath = self.saveScreenRegion(regionName=None, regionRect=rect)
        if pilImage.format == "PNG":
            pilImage = pilImage.convert("RGB")
        pilImage.save(refImagePath)
        self.__imageManager.updateThumbnail(refImagePath)

    def checkScreen(self, navigator, screen, checkVersions=True):
        rc = self.openNavigator(navigator)
        if not rc:
            print("openNavigator failed")
            return False

        if screen not in self.navigatorScreenList:
            msg = "checkScreen: Navigator.Screen missing %s.%s " % (self.navigatorName, screen)
            raise Exception(msg)

        if self.modelType.X3() and self.hdServer:
            if self.__screenComparer is None:
                from screenCompare import ScreenCompare
                self.__screenComparer = ScreenCompare()
                self.__screenComparer.imagePath = self.saveScreen()
                self.__screenComparer.checkVersions = checkVersions

        if checkVersions:
            validateScreenList = self.getAllScreens(self.navigatorName, screen)
            for screen in validateScreenList:
                rc, rcComment = self.checkScreen(self.navigatorName, screen, checkVersions=False)
                if rc:
                    break
            if self.__screenComparer:
                self.__screenComparer.cleanup()
                self.__screenComparer = None
            return rc, rcComment

        screenName = "%s.%s" % (self.navigatorName, screen)
        if self.__screenComparer:
            naviSDO = self.convertNavigatorToScreenDef(screen)
            print("ScreenComparer.compare", screen)
            resultListScreen = self.__screenComparer.compare(naviSDO)
        else:
            resultListScreen = self.__api.ValidateNavigatorScreen(screen, self.slotNo)
        print(("ValidateNavigatorScreen: {} {}").format(screenName, resultListScreen))

        rc = resultListScreen[0]
        regions = resultListScreen[1]
        comment = ""
        for r in regions:
            # print r
            rName = r[0]
            rMatch = r[1]
            v = "-- undef --"
            k = "ImageSimilarity"
            if k in list(r[2].keys()):
                v = r[2][k]
                if not rc:
                    self.logReferenceScreenRegions(screen, rName)
            k = "Detected Peak Error"
            if k in list(r[2].keys()):
                v = r[2][k]

            if v == "-- undef --":
                v = -999.0
            commentStr = "rName:%s, rMatch:%s, %s:%.1f" % (rName, rMatch, k, v)
            if len(comment) == 0:
                comment = commentStr
            else:
                comment = "%s;%s" % (comment, commentStr)

        if self.__screenComparer:
            if not self.__screenComparer.checkVersions:
                self.__screenComparer.cleanup()
                self.__screenComparer = None
        return rc, comment

    def setCaptureToAlways(self, sdo):
        """
        Set the return screen parameter of the screen definition so that we always get screen capture
        sdo input: Screen Definition Object
        """

        # recursively enable capture on the screen def objects
        sdo.ReturnScreenImage = self.__api.ReturnScreen.Always
        # check for embedded SDOs
        for sdo_in in sdo.Regions:
            if isinstance(sdo_in, self.__api.ScreenDefinition):
                self.setCaptureToAlways(sdo_in)

    def getModelName(self):
        model = self.slotInfoDict['Model']
        if model == "Jupiter":
            model = "Ethan"
        if model == "Hamburg":
            model = "Ethan"
        if model == "Amidala":
            model = "Ethan"
        return model

    def __ocrTesseract(self, imagePath):
        if imagePath is None:
            print("ERROR: __ocrTesseract imagePath is None ")
            return None
        outputs = {}
        (outputs['SuspiciousSymbols'],
            outputs['UnrecognisedSymbols'],
            outputs['AllSymbols'],
            outputs['AllWords'],
            outputs['ObtainedString']) = self.__tocrClient.run(imagePath)
        ocrString = outputs['ObtainedString']
        # print ocrString
        return ocrString

    def __readOCR_tesseract(self, regionRect=None):
        if self.__saveScreenRegions:
            imagePath = self.saveScreenRegion(None, regionRect)
        else:
            self.__saveScreenRegions = True
            imagePath = self.saveScreenRegion(None, regionRect)
            self.__saveScreenRegions = False
        ocrString = self.__ocrTesseract(imagePath)
        return ocrString

    def readOCR(self, ocrRegionName, regionRect=None):
        model = self.getModelName()
        self.__api.OCRSetLanguage('deu')  # set language

        print("readOCR: ocrRegionName=%s regionRect=%s" % (ocrRegionName, regionRect))
        if ocrRegionName is not None:
            regionName = "/%s/%s" % (model, ocrRegionName)
            region = self.__api.FindNamedRegion(regionName)
            try:
                region = region.LookupBySlot(self.slotNo)
            except:
                region = None
            if region is None:
                msg = "readOCR: regionName (%s) does not exist " % (regionName)
                print("ERROR: %s" % (msg))
                raise Exception(msg)
            self.saveScreenRegion(regionName)
        else:
            region = regionRect
            if self.__useTesseract:
                return self.__readOCR_tesseract(regionRect)
            self.saveScreenRegion(None, regionRect)

        outputs = {}
        (outputs['SuspiciousSymbols'],
            outputs['UnrecognisedSymbols'],
            outputs['AllSymbols'],
            outputs['AllWords'],
            outputs['ObtainedString']) = self.__api.OCRSlot(region, self.slotNo)
        ocrString = outputs['ObtainedString']
        # print ocrString
        return ocrString

    def __readOCRImage_tesseract(self, image, regionRect=None):
        '''
            OCR Webservice on Linux need bmp or png, use png
            OCR Webservice on Windows supports all formats, use jpg
        '''
        imageExtension = "jpg"
        imageExtension = "png"
        if isinstance(image, self.__api.Imaging.StormTestImageObject):
            pilImage = image.ToPILImage()
        else:
            pilImage = image

        if regionRect:
            img_w, img_h = pilImage.size
            (x, y, w, h) = regionRect
            print("__readOCRImage_tesseract: pilImage.shape=(%s,%s) regionRect=%s" % (img_w, img_h, regionRect))
            if (x + w) < img_w and (y + h) < img_h:
                cropArea = (x, y, x + w, y + h)
                pilImage = pilImage.crop(cropArea)
            else:
                print("WARNING: __readOCRImage_tesseract: pilImage.shape=(%s,%s) regionRect=%s" % (img_w, img_h, regionRect))

        nowSecsStr = "%s" % time.time()
        nowSecsStr = nowSecsStr.replace(".", "_")
        imageName = "img_ocr_%s.%s" % (nowSecsStr, imageExtension)
        imagePath = os.path.join(self.logPath, imageName)
        print("__readOCRImage_tesseract: %s" % (imagePath))
        pilImage.save(imagePath)

        ocrString = self.__ocrTesseract(imagePath)
        return ocrString

    def readOCRImage(self, image, regionRect=None):
        self.__api.OCRSetLanguage('deu')  # set language
        if self.__useTesseract:
            return self.__readOCRImage_tesseract(image, regionRect)

        outputs = {}
        (outputs['SuspiciousSymbols'],
            outputs['UnrecognisedSymbols'],
            outputs['AllSymbols'],
            outputs['AllWords'],
            outputs['ObtainedString']) = self.__api.OCRImage(image, regionRect)
        ocrString = outputs['ObtainedString']
        # print ocrString
        return ocrString

    def stormtestMatchStrings(self, refStr, ocrStr, threshold):
        print("matchStrings: refStr={} ocrStr={}".format(refStr, ocrStr))
        method = 1
        if method == 1:
            difference = self.__api.ComputeStringsDistance(refStr, ocrStr)
            # print difference
            if difference == 0:
                # total match
                print("matchStrings: return True -> total match")
                return True
            relMatch = len(refStr) - difference
            pcMatch = (float(relMatch) / len(refStr)) * 100
            # print "Percentage Match = %.1f" % (pcMatch)
            if float(pcMatch) > float(threshold):
                rc = True
            else:
                rc = False

            print("matchStrings: return %s percentage/threshold = %.1f/%s" % (rc, pcMatch, threshold))

        if method == 2:
            rc = self.__api.CompareStrings(refStr, ocrStr, threshold)
            print(rc)
        return rc

    def powerOn(self):
        self.keysPressed.append("Power ON")
        if self.objReporter:
            if self.stormtestClient.objReporter != None:
                self.objReporter.objTestHeartBeats.updateIR("Power ON")
        self.__api.PowerOnSTB(5, self.slotNo)
        self.saveScreen("PowerOnSTB")

    def powerOff(self):
        self.keysPressed.append("Power OFF")
        if self.objReporter:
            if self.stormtestClient.objReporter != None:
                self.objReporter.objTestHeartBeats.updateIR("Power OFF")
        self.__api.PowerOffSTB(5, self.slotNo)
        self.saveScreen("PowerOffSTB")

    def zappingTime(self, sTargetService=None, triggerButton=None, frameName=None):
        '''
        Trigger on the last digit of the target service
        or just the trigger button
        KeyPress -> black screen -> non black screen
        Time measured from key press to first non black screen
        '''
        if sTargetService is None and triggerButton is None:
            print("ERROR: no target service defined and no trigger button defined")
            return -1

        if sTargetService is not None and triggerButton is not None:
            print("ERROR: Both target service defined and trigger button defined")
            return -1

        ret = self.__api.GetRawInputInfo(self.slotNo)
        framesPerSec = int(ret['HardwareCaptureRate'])
        print("framesPerSec: %s" % (framesPerSec))
        # Reserve High Speed Timer
        if not self.__api.ReserveVideoTimer():
            print("ERROR: High Speed Video Timer failed")
            return None

        print("Reserve High Speed Video Timer")
        zapstatus = self.__api.EnableCaptureZapFrames(maxFrames=250, startFrame=0, skipCount=0, slotNo=self.slotNo)
        rc = zapstatus[0][1]
        if not rc:
            return -1
        self.__api.WaitSec(2)

        if sTargetService:
            keyLen = len(sTargetService)
            if sTargetService[0] == "1" and not self.modelType.LLAMA():
                for i in range(keyLen):
                    self.pressButton(sTargetService[i], 300)
                triggerButton = "Ok"
                triggerButton = self.remapKey(triggerButton)
            else:
                for i in range(keyLen - 1):
                    self.pressButton(sTargetService[i], 300)
                triggerButton = sTargetService[keyLen - 1]

        # Setup to trigger on the selected keypress
        triggerStatus = self.__api.TriggerHighSpeedTimer(triggerButton, 0, 12, slotNo=self.slotNo)
        rc = triggerStatus[0][1]
        if not rc:
            return -1

        # Press the button
        self.keysPressed.append("%s/0s" % (triggerButton))
        if self.objReporter:
            if self.stormtestClient.objReporter != None:
                self.objReporter.objTestHeartBeats.updateIR("%s/0s" % (triggerButton))
        self.__api.PressButton(triggerButton)
        # wait long enough for it to capture all frames
        self.__api.WaitSec(8)

        imageCount = self.__api.GetCountImagesSaved(self.slotNo)
        frameCount = imageCount[0][1]
        print("frameCount: %s" % (frameCount))

        # get resources needed
        if self.hdServer:
            blackColor = (0, 0, 0)
            tolerances = (20, 20, 20)
            flatness = 90
            peakError = 2.0
            blackRegion = [465, 301, 909, 381]
        else:
            model = self.getModelName()
            resourcePath = "/%s/%s" % (model, "zapColor")
            blackColor = self.__api.FindNamedColor(resourcePath)
            resourcePath = "/%s/%s" % (model, "zapRegion")
            blackRegion = self.__api.FindNamedRegion(resourcePath)

        zapTime = float(-1.0)
        inBlackSection = False
        endFrame = -1
        for i in range(frameCount):
            returnFrame = self.__api.GetRawZapFrame(i)
            if returnFrame is None:
                continue
            if self.useMagiq:
                image = self.loadSTimageObjectFromFile(returnFrame)
            else:
                image = returnFrame[0][1]
                if frameName is not None:
                    filename = "%s-%.3d.png" % (frameName, i)
                    image.Save(filename)

            if image is None:
                print("image is None at index %s/%s" % (i, frameCount))
                continue

            # Check the colour of the given region
            if self.hdServer:
                ret = self.__api.CompareColorEx(image, blackColor,
                                            tolerances=tolerances,
                                            flatness=flatness,
                                            peakError=peakError,
                                            includedAreas=blackRegion)
            else:
                ret = self.__api.CompareColorEx(image, blackColor, includedAreas=blackRegion)

            # print "CompareColorEx: %s %s" % (i, ret)
            if ret[0]:
                if not inBlackSection:
                    print("Start of black section: in frame %s" % (i))
                    inBlackSection = True
            else:
                if inBlackSection:
                    print("End of black section: in frame %s" % (i))
                    inBlackSection = True
                    endFrame = i
                    break

        if self.__api.FreeVideoTimer():
            print("High Speed Video Timer freed")

        if endFrame > 0:
            zapTime = float(endFrame) / framesPerSec

        print("zapTime: %s" % (zapTime))
        return zapTime

    def compareColor(self, image, referenceColor, tolerance, flatness=70, peakError=2, region=None):
        '''
        image - usually cropped part of bigger image

        blackColor = [0, 0, 0]
        blackRegion = [160, 173, 1558, 634]

        Type (tolerance[0],tolerance[1],tolerance[2]): <type 'tuple'>
        Type flatness: <type 'float'>
        Type peakError: <type 'float'>

        return:
            retArray = [rc, actual_color, actual_flatness, actual_peak_error]
        '''
        refImage = image
        if isinstance(image, str):
            refImage = self.getSoakroomNASpath(image)

        retArray = self.__api.CompareColorEx(refImage, referenceColor, tolerance, flatness=flatness, peakError=peakError,
                                            includedAreas=region)

        return retArray

    def zappingTimeCheckImage(self, sTargetImage=None, triggerButton=None, frameName=None, rect=None, durationSecs=8):
        '''
        Trigger on the last digit of the target service
        or just the trigger button
        KeyPress -> black screen -> non black screen
        Time measured from key press to first non black screen
        '''
        if sTargetImage is None and triggerButton is None:
            print("ERROR: no target service defined and no trigger button defined")
            return -1

        ret = self.__api.GetRawInputInfo(self.slotNo)
        framesPerSec = int(ret['HardwareCaptureRate'])
        print("framesPerSec: %s" % (framesPerSec))
        # Reserve High Speed Timer
        if not self.__api.ReserveVideoTimer():
            print("ERROR: High Speed Video Timer failed")
            return None

        print("Reserve High Speed Video Timer")
        zapstatus = self.__api.EnableCaptureZapFrames(maxFrames=250, startFrame=0, skipCount=0, slotNo=self.slotNo)
        rc = zapstatus[0][1]
        if not rc:
            return -1
        self.__api.WaitSec(2)

        # Setup to trigger on the selected keypress
        triggerStatus = self.__api.TriggerHighSpeedTimer(triggerButton, 0, 12, slotNo=self.slotNo)
        rc = triggerStatus[0][1]
        if not rc:
            return -1

        # Press the button
        self.keysPressed.append("%s/0s" % (triggerButton))
        if self.objReporter:
            if self.stormtestClient.objReporter != None:
                self.objReporter.objTestHeartBeats.updateIR("%s/0s" % (triggerButton))
        self.__api.PressButton(triggerButton)
        # wait long enough for it to capture all frames
        self.__api.WaitSec(durationSecs)

        imageCount = self.__api.GetCountImagesSaved(self.slotNo)
        frameCount = imageCount[0][1]
        print("frameCount: %s" % (frameCount))

        zapTime = float(-1.0)
        endFrame = -1
        for i in range(frameCount):
            returnFrame = self.__api.GetRawZapFrame(i)
            if self.useMagiq:
                image = self.loadSTimageObjectFromFile(returnFrame)
            else:
                image = returnFrame[0][1]
                if frameName is not None:
                    filename = "%s-%.3d.png" % (frameName, i)
                    image.Save(filename)

            # Check the comparison of the given sTargetImage
            ret = self.compareImage(sTargetImage, image, region=rect, percent=75)
            if ret:
                print("Found image: in frame %s" % (i))
                endFrame = i
                break

        if self.__api.FreeVideoTimer():
            print("High Speed Video Timer freed")

        if endFrame > 0:
            zapTime = float(endFrame) / framesPerSec

        print("zapTime: %s" % (zapTime))
        return zapTime

    def waitScreenDefMatch(self, sdo, timeToWaitSec, waitGapSec):
        [sdo, timeWaitedSec, capNumber] = self.__api.WaitScreenDefMatch(screenDef=sdo, timeToWait=timeToWaitSec, waitGap=waitGapSec, slotNo=self.slotNo)
        return sdo, timeWaitedSec, capNumber

    def zappingTimeCheckScreen(self, sTargetScreenName=None, triggerButton=None, frameName=None, navigator=None, lowAccuracy=True):
        '''
        sTargetScreenName - could be string or sdo
        To be executed before the last key press of an action, labelling the final key press as the triggerButton
        KeyPress -> loading app/process -> target frame
        Time measured from key press to matching screen from nav
        (If the time is under 9 sec it will be measured precisely by frame, if longer it will have a potential inaccuracy of +/-0.2 sec
        '''
        maxWaitTime = 50

        # Handle potential input errors
        if sTargetScreenName is None:
            print("ERROR: no target app defined")
            return -1

        if triggerButton is None:
            print("ERROR: no trigger button defined")
            return -1

        if isinstance(sTargetScreenName, str):
            print("sTargetScreenName is string")

            # Convert Navigator Screen to sdo object
            if navigator is None:
                navigator = "Ethan"
            self.openNavigator(navigator)
            sdo = self.convertNavigatorToScreenDef(sTargetScreenName)
        else:
            print("sTargetScreenName is object")
            sdo = sTargetScreenName

        # Check frame rate
        ret = self.__api.GetRawInputInfo(self.slotNo)
        framesPerSec = int(ret['HardwareCaptureRate'])
        print("framesPerSec: %s" % (framesPerSec))

        # Reserve high speed timer
        if not self.__api.ReserveVideoTimer():
            print("ERROR: High Speed Video Timer failed")
            return None

        # Set the trigger button
        # Press the trigger button
        # Wait for all frames to capture
        self.__api.EnableCaptureZapFrames(maxFrames=250, startFrame=0, skipCount=0, slotNo=self.slotNo)
        zapStatus = self.__api.TriggerHighSpeedTimer(irKey=triggerButton, keyCount=0, timeout=12, slotNo=self.slotNo)
        rc = zapStatus[0][1]
        if not rc:
            return None
        self.__api.WaitSec(1)
        self.keysPressed.append("%s/0s" % (triggerButton))
        if self.objReporter:
            if self.stormtestClient.objReporter != None:
                self.objReporter.objTestHeartBeats.updateIR("%s/0s" % (triggerButton))
        self.__api.PressButton(triggerButton)
        timeFrameForChangesSec = 9
        self.__api.WaitSec(timeFrameForChangesSec)

        maxLongTermMeasurement = 50

        # Low accuracy timer
        if lowAccuracy:
            retMatchingSDO = self.__api.WaitScreenDefMatch(screenDef=sdo, timeToWait=maxLongTermMeasurement, waitGap=0.1, slotNo=self.slotNo)
            print("SDO match delay: " + str(retMatchingSDO[1]))
            zapTime = retMatchingSDO[1] + timeFrameForChangesSec
            retMatchingSDO[0].Close()
            self.saveScreen()
        else:
            self.saveScreen()
            self.__api.WaitSec(2)
            zapTime = -1

        imageCount = self.__api.GetCountImagesSaved(self.slotNo)
        numFrames = imageCount[0][1]
        print("numFrames: %s" % (numFrames))

        frame = self.__api.FindRawZapMatch(sdo, 0, numFrames)[0][2]
        if frame is not None:
            print("Match found at frame ", frame)
            zapTime = float(frame) / framesPerSec

            if frameName is not None:
                for j in range(frame - 4, frame + 4):
                    if j < 250:
                        returnFrame = self.__api.GetRawZapFrame(j)
                        if self.useMagiq:
                            image = self.loadSTimageObjectFromFile(returnFrame)
                        else:
                            image = returnFrame[0][1]
                            # save it
                            filename = str(frameName) + str(j) + ".png"
                            image.Save(filename)
                            print("save frame no. ", j)
                    else:
                        break

        else:
            for frame_log_index in range(250)[::framesPerSec]:

                if frame_log_index == 0:
                    continue

                if frameName is not None:
                    returnFrame = self.__api.GetRawZapFrame(frame_log_index)
                    if self.useMagiq:
                        image = self.loadSTimageObjectFromFile(returnFrame)
                    else:
                        image = returnFrame[0][1]
                        # save it
                        filename = str(frameName) + str(frame_log_index) + ".png"
                        image.Save(filename)
                        print("Save frame at sec. ", (frame_log_index / framesPerSec) - 1)

        self.__api.FreeVideoTimer()

        if isinstance(sTargetScreenName, str):
            sdo.Close()

        if ((zapTime) >= maxWaitTime):
            zapTime = -1  # not valid measurement

        print("zapTime: %s" % (zapTime))
        return zapTime

    def initialised(self):
        if not self.useStormtest:
            # print "useRegions(): useStormtest is false"
            return False

        if not self.connected:
            # print "useRegions(): connected is false"
            return False

        return True

    def beginLogRegion(self, logRegionName):
        if not self.initialised():
            return False

        self.__api.BeginLogRegion(logRegionName)
        return True

    def endLogRegion(self, logRegionName, logRegionStyle, comment):
        if not self.initialised():
            return False

        stLogRegionStyle = self.__translateLogRegionStyle(logRegionStyle)
        self.__api.EndLogRegion(logRegionName, stLogRegionStyle, comment)
        return True

    def __translateLogRegionStyle(self, logRegionStyle):
        sLogRegionStyle = str(logRegionStyle)
        if sLogRegionStyle.lower() == "pass":
            return self.__api.LogRegionStyle.Pass
        if sLogRegionStyle.lower() == "fail":
            return self.__api.LogRegionStyle.Fail
        if sLogRegionStyle.lower() == "warn":
            return self.__api.LogRegionStyle.Warn
        if sLogRegionStyle.lower() == "serial":
            return self.__api.LogRegionStyle.Serial
        if sLogRegionStyle.lower() == "observe":
            return self.__api.LogRegionStyle.Observe
        if sLogRegionStyle.lower() == "console":
            return self.__api.LogRegionStyle.Console
        if sLogRegionStyle.lower() == "verbose":
            return self.__api.LogRegionStyle.Verbose
        if sLogRegionStyle.lower() == "entry":
            return self.__api.LogRegionStyle.Entry

    def getScreenList(self, navigator=None):
        rc = self.openNavigator(navigator)
        if not rc:
            return None

        return self.navigatorScreenList

    def getScreenRegionDict(self, screenName, navigator=None):
        self.openNavigator(navigator)
        if screenName not in self.navigatorScreenList:
            msg = "getScreenRegionDict: Navigator.Screen missing %s.%s " % (self.navigatorName, screenName)
            raise Exception(msg)

        regionDict = {}
        sdo = self.__api.ConvertNavigatorToScreenDef(screenName, self.slotNo)
        for r in sdo.Regions:
            # print r.Name, r.Rect
            sdoDict = {}
            sdoDict['type'] = None
            if isinstance(r, self.getImageRegion()):
                sdoDict['type'] = "ImageRegion"
            if isinstance(r, self.getOCRRegion()):
                sdoDict['type'] = "OCRRegion"
            if isinstance(r, self.getColorRegion()):
                sdoDict['type'] = "ColorRegion"
            if self.useMagiq:
                sdoDict['sdo'] = r
            else:
                sdoDict['sdo'] = r.Clone()
            regionDict[r.Name] = sdoDict

        sdo.Close()
        return regionDict  # {'reg name 1': {'sdo':sdo, 'type': ColorRegion/OCRRegion/ImageRegion}, 'reg name 2':...}

    def getZappingImages2(self, triggerButton=None, timeFrameForChagesSec=10):
        '''
        triggerButton = Last key press before the 10sec of frame capture will begin
        return        = List of all the frames as images in order of capture
        '''
        if triggerButton is None:
            print("ERROR: triggerButton is not defined")
            return None

        # Reserve high speed timer
        if not self.__api.ReserveVideoTimer():
            print("ERROR: High Speed Video Timer failed")
            return None

        # Set the trigger button
        # Press the trigger button
        # Wait for all frames to capture
        self.__api.EnableCaptureZapFrames(maxFrames=250, startFrame=0, skipCount=0, slotNo=self.slotNo)
        zapStatus = self.__api.TriggerHighSpeedTimer(irKey=triggerButton, keyCount=0, timeout=12, slotNo=self.slotNo)
        rc = zapStatus[0][1]
        if not rc:
            return None
        self.__api.WaitSec(1)
        self.keysPressed.append("%s/0s" % (triggerButton))
        if self.objReporter:
            if self.stormtestClient.objReporter != None:
                self.objReporter.objTestHeartBeats.updateIR("%s/0s" % (triggerButton))
        self.__api.PressButton(triggerButton)
        self.__api.WaitSec(timeFrameForChagesSec)

        imageCount = self.__api.GetCountImagesSaved(self.slotNo)
        numFrames = imageCount[0][1]
        print("numFrames: %s" % (numFrames))
        return numFrames

    def getRawZapFrame(self, idx):
        returnFrame = self.__api.GetRawZapFrame(idx)
        return returnFrame

    def freeVideoTimer(self):
        self.__api.FreeVideoTimer()

    def getZappingImages(self, triggerButton=None, timeFrameForChagesSec=10):
        '''
        triggerButton = Last key press before the 10sec of frame capture will begin
        return        = List of all the frames as images in order of capture
        '''
        if triggerButton is None:
            print("ERROR: triggerButton is not defined")
            return None

        imageList = []

        # Reserve high speed timer
        if not self.__api.ReserveVideoTimer():
            print("ERROR: High Speed Video Timer failed")
            return None

        # Set the trigger button
        # Press the trigger button
        # Wait for all frames to capture
        self.__api.EnableCaptureZapFrames(maxFrames=250, startFrame=0, skipCount=0, slotNo=self.slotNo)
        zapStatus = self.__api.TriggerHighSpeedTimer(irKey=triggerButton, keyCount=0, timeout=12, slotNo=self.slotNo)
        rc = zapStatus[0][1]
        if not rc:
            return None
        self.__api.WaitSec(1)
        self.keysPressed.append("%s/0s" % (triggerButton))
        if self.objReporter:
            if self.stormtestClient.objReporter != None:
                self.objReporter.objTestHeartBeats.updateIR("%s/0s" % (triggerButton))
        self.__api.PressButton(triggerButton)
        self.__api.WaitSec(timeFrameForChagesSec)

        imageCount = self.__api.GetCountImagesSaved(self.slotNo)
        numFrames = imageCount[0][1]
        print("numFrames: %s" % (numFrames))

        for j in range(numFrames):
            returnFrame = self.__api.GetRawZapFrame(j)
            if self.useMagiq:
                image = self.loadSTimageObjectFromFile(returnFrame)
            else:
                image = returnFrame[0][1]
            # Append it to imageList
            imageList.append(image)
            print("Appended frame no. ", j)
        print("Finished Appending")

        self.__api.FreeVideoTimer()
        return imageList

    def captureSTIO(self, rect, filename=None, imageQuality=80):
        '''
        rect      =  A set of coordinates or NamedRegion
        filename  =  The filename specifies where to save the file and allows d t to substitute the date/time. If 'None' for filename, then the file is not saved, just captured to memory.
        imageQuality = range between 1-100
        return StormtestImageObject
        '''
        if not filename:
            nowSecsStr = "%s" % time.time()
            nowSecsStr = nowSecsStr.replace(".", "_")
            filename = "img_%s.jpg" % (nowSecsStr)

        rc = self.captureImageEx(rect, filename, imageQuality)
        return rc[0][2]

    def compareImage(self, refImage, testImage, region=None, percent=80):
        '''
        refImage  =  The base image to be compared to
        testImage =  The image being compared
        region    =  A NamedRegion or Rectangle where the comparison will take place
        percent   =  The threshold for a comparison to pass
        return    =  Bool, stating whether the comparison passed the threshold
        '''
        if isinstance(refImage, str):
            refImage = self.getSoakroomNASpath(refImage)
        if isinstance(testImage, str):
            testImage = self.getSoakroomNASpath(testImage)

        if region is None:
            rc = self.__api.CompareImageEx(refImage, testImage, percent=percent)
        else:
            rc = self.__api.CompareImageEx(refImage, testImage, percent=percent, includedAreas=region)

        print("Actual percentage match:  %.2f  Threshold is: %s" % (rc[1], percent))
        return rc[0]

    def __captureImageWrapper(self, rect, f, imageQuality):
        try:
            print("__captureImageWrapper: rect=%s f=%s imageQuality=%s" % (rect, f, imageQuality))
            retVal = self.__api.CaptureImageEx(rect, f, imageQuality)
            print("__captureImageWrapper: retVal=%s" % (pformat(retVal)))
        except:
            tb = traceback.format_exc()
            print("Exception: __captureImageWrapper: %s" % (tb))
            self.waitSecs(2)
            retVal = None
        return retVal

    def __captureImageEx(self, rect, f, imageQuality):
        try:
            maxLoops = 2
            for __ in range(maxLoops):
                retVal = self.__captureImageWrapper(rect, f, imageQuality)
                if retVal:
                    break
                retVal = self.__api.CaptureImageEx(rect, None, imageQuality)
                print("__captureImageEx: retVal=%s" % (pformat(retVal)))
                if retVal[0][1]:
                    stio = retVal[0][2]
                    print("save start")
                    filenamePath = os.path.join(self.logPath, f)
                    r = stio.Save(filenamePath)
                    retVal[0][3] = filenamePath
                    print("save end " + str(r))
                    break

            if retVal:
                return retVal

        except:
            print("Exception: __captureImageEx rect=%s f=%s imageQuality=%s" % (rect, f, imageQuality))
            tb = traceback.format_exc()
            print("__captureImageEx: %s" % (tb))
            msg = "self.__api.CaptureImageEx: failed "
            raise Exception(msg)

        return retVal

    def __useScreenResizing(self, rect):
        '''
        Resolve the black edges by using a splitter and not using the UHD Downscalar
        Only support for HD
        '''
        _slotsRequiringResizing = [ 80101,
                                  80103
                                  ]
        slotsRequiringResizing = []
        if self.slot_id in slotsRequiringResizing and rect is None:
            return True
        return False

    def captureImageEx(self, rect, filename, imageQuality=80):

        f = os.path.basename(filename)
        print("captureImageEx: rect=%s filename=%s" % (rect, f))

        if self.__useScreenResizing(rect):
            ret = self.screenshotAndResize(rect, f, imageQuality)

            if self.objReporter:
                if self.stormtestClient.objReporter != None:
                    self.objReporter.objTestHeartBeats.updateStep(imagePath=ret[0][3])
            return ret
        else:
            ret = self.__captureImageEx(rect, f, imageQuality)

            if self.objReporter:
                if self.stormtestClient.objReporter != None:
                    self.objReporter.objTestHeartBeats.updateStep(imagePath=ret[0][3])
            return ret

    def convertNavigatorToScreenDef(self, screenToConvert):
        if screenToConvert not in self.navigatorScreenList:
            msg = "convertNavigatorToScreenDef: Navigator.Screen missing %s.%s " % (self.navigatorName, screenToConvert)
            raise Exception(msg)
        return self.__api.ConvertNavigatorToScreenDef(screenToConvert, self.slotNo)

    def screenDefMatchImage(self, sdoScreen, imageScreenshot):
        if isinstance(sdoScreen, str):
            sdoScreen = self.getSoakroomNASpath(sdoScreen)
        if isinstance(imageScreenshot, str):
            imageScreenshot = self.getSoakroomNASpath(imageScreenshot)

        return self.__api.ScreenDefMatchImage(sdoScreen, imageScreenshot)

    def getImageRegionType(self):
        return self.__api.ImageRegion

    def getCurrentNavigator(self, slot):
        return self.__api.GetCurrentNavigator(slot)

    def isUnderDaemon(self):
        return self.__api.IsUnderDaemon()

    def getPhysicalAllocations(self):
        return self.__api.GetPhysicalAllocations()

    def setDebugLevel(self, trace, level):
        return self.__api.SetDebugLevel(trace, level)

    def writeDebugLine(self, commentToLog, debugLevel=None):
        strDebugLevel = str(debugLevel).upper()
        debugLevel = self._getDebugLevel(strDebugLevel)
        return self.__api.WriteDebugLine(commentToLog, debugLevel)

    def _getDebugLevel(self, strDebugLevel):
        if strDebugLevel == "INFO":
            return self.__api.DebugLevel.INFO
        if strDebugLevel == "NONE":
            return self.__api.DebugLevel.NONE
        if strDebugLevel == "ERROR":
            return self.__api.DebugLevel.ERROR
        if strDebugLevel == "WARNING":
            return self.__api.DebugLevel.WARNING
        if strDebugLevel == "VERBOSE":
            return self.__api.DebugLevel.VERBOSE

        return -1

    def getNamedString(self):
        return self.__api.stormtest_client.NamedString

    def getNamedRegion(self):
        return self.__api.stormtest_client.NamedRegion

    def getImageRegion(self):
        return self.__api.ImageRegion  # __api.stormtest_client.ImageRegion

    def getNamedImage(self):
        return self.__api.stormtest_client.NamedImage

    def getOCRRegion(self):
        return self.__api.OCRRegion

    def getColorRegion(self):
        return self.__api.ColorRegion

    def getNamedColor(self):
        return self.__api.stormtest_client.NamedColor

    def getMotionRegion(self):
        return self.__api.MotionRegion

    def getAudioRegion(self):
        return self.__api.AudioRegion

    def getScreenDefinition(self):
        return self.__api.ScreenDefinition

    def getScreenDefinitionObj(self):
        return self.__api.ScreenDefinition()

    def readNamedRegion(self, regionPath):
        return self.__api.ReadNamedRegion(regionPath)

    def getVideoParams(self):
        if self.useMagiq:
            ret = self.__api.ListStreams()
            idx = ret["default"]
            params = ret["list"][idx]
            videoParamsDict = {}
            videoParamsDict['BitRate'] = params["max_bitrate"]
            videoParamsDict['Resolution'] = "%s x %s" % (params["res_w"], params["res_h"])
            videoParamsDict['FrameRate'] = params["fps"]
            self.__videoParams = videoParamsDict
            return videoParamsDict

        ret = self.__api.GetResolution(self.slotNo)
        res = ret
        print("GetResolution: %s" % (ret))
        ret = self.__api.GetFrameRate(self.slotNo)
        fps = ret
        print("GetFrameRate: %s" % (ret))
        ret = self.__api.GetMaxBitRate(self.slotNo)
        br = ret
        print("GetMaxBitRate: %s" % (ret))

        videoParamsDict = {}
        videoParamsDict['BitRate'] = br
        videoParamsDict['Resolution'] = res
        videoParamsDict['FrameRate'] = fps
        self.__videoParams = videoParamsDict
        return videoParamsDict

    def setVideoParams(self, videoParamsDict=None):
        if self.__videoParams is None:
            self.getVideoParams()

        if videoParamsDict is None:
            # set to default
            videoParamsDict = {}
            videoParamsDict['BitRate'] = 256000
            videoParamsDict['Resolution'] = "1920x1080"

        getAgain = False
        k = "BitRate"
        if k in list(videoParamsDict.keys()):
            v = videoParamsDict[k]
            currentV = self.__videoParams[k]
            if currentV == v:
                print("setVideoParams: %s - No change - %s " % (k, v))
            else:
                self.__api.SetMaxBitRate(v, self.slotNo)
                getAgain = True
        k = "Resolution"
        if k in list(videoParamsDict.keys()):
            v = videoParamsDict[k]
            currentV = self.__videoParams[k].replace(" x ", "x")
            if currentV == v:
                print("setVideoParams: %s - No change - %s " % (k, v))
            else:
                self.__api.SetResolution(v, self.slotNo)
                getAgain = True

        if getAgain:
            self.getVideoParams()

    def startVideoLogRecording(self, useHighBitrate=False, useHighBitrate2=False, useLowBitrate=False):
        if not self.initialised():
            return False, ""

        self.stopVideoLogRecording()
        print("startVideoLogRecording")
        if useHighBitrate:
            self.__api.SetResolution("4CIF", self.slotNo)
            self.__api.SetMaxBitRate(3000000, self.slotNo)
            self.__api.SetFrameRate(25, self.slotNo)

        if useHighBitrate2:
            self.__api.SetResolution("4CIF", self.slotNo)
            self.__api.SetMaxBitRate(8000000, self.slotNo)
            self.__api.SetFrameRate(25, self.slotNo)

        if useLowBitrate:
            self.__api.SetResolution("CIF", self.slotNo)
            self.__api.SetMaxBitRate(512000, self.slotNo)
            self.__api.SetFrameRate(25, self.slotNo)

        print("before StartVideoLog")
        ret = self.__api.StartVideoLog()
        print("after StartVideoLog")
        print(ret)
        videoFile = None
        rc = ret[0][1]
        if rc:
            videoFile = ret[0][2]
            print("Path only: " + videoFile)
            ftpPath = self.getNASurl(videoFile)
            # Use VSPlayer to open video
            print("VSPlayer path: " + ftpPath)
            self.printHTMLlink(ftpPath)
            self.videoLogRunning = True
        return rc, videoFile

    def printHTMLlink(self, objPath):
        '''
        Change
        C:\workspace\logs\logs_539\ethan_DAZN_v2_stability_20210429_194153_088887\img_1619718324_7.jpg
        to
        http://172.20.116.70:8091/logs/vtSued/ethan_DAZN_v2_stability_20210429_194153_088887/img_1619718324_7.jpg

        and
        C:\workspace\logs\logs_539\ethan_DAZN_v2_stability_20210429_194153_088887\Vid_2_2021-04-29_19.45.25.avi
        to
        http://172.20.116.70:8091/logs/vtSued/ethan_DAZN_v2_stability_20210429_194153_088887/Vid_2_2021-04-29_23.34.58.avi
        '''
        uncPath = objPath.replace("\\", "/")
        if "WIN10-SOAKROOM" not in self.host:
            return
        if "C:/workspace/logs" not in uncPath:
            return

        bn = os.path.basename(self.logPath)
        itemPath = re.sub("C:/workspace/logs/.*/%s/" % (bn), "", uncPath)
        nasURL = "http://%s:8091/logs/vtSued/%s/%s" % (self.NASip, bn, itemPath)
        hrefComment = "<a target='_blank' href='%s'>HTML Link</a>" % (nasURL)
        print(hrefComment)

    def getNASurl(self, uncPath):
        uncPath = uncPath.replace("\\", "/")
        nasURL = "http://%s:8091/logs/" % (self.NASip)
        if "vtSued" in uncPath:
            fn = "//172.20.116.70/log-file/vtSued/"
            nasURL = "http://%s:8091/logs/vtSued/" % (self.NASip)
            nasURL = uncPath.replace(fn, nasURL)
        else:
            nasURL = uncPath.replace("//SOAKROOM-NAS/log-file/", nasURL)
        nasURL = nasURL.replace("\\", "/")
        return nasURL

    def getSoakroomNASpath(self, url):
        if "http" not in url:
            return url
        if "vtSued" in url:
            fn = "//172.20.116.70/log-file/vtSued/"
            nasURL = "http://%s:8091/logs/vtSued/" % (self.NASip)
            nasPath = url.replace(nasURL, fn)
        else:
            nasURL = "http://%s:8091/logs/" % (self.NASip)
            nasPath = url.replace(nasURL, "\\\\SOAKROOM-NAS\\log-file\\")
        nasPath = nasPath.replace("/", "\\")
        return nasPath

    def stopVideoLogRecording(self):
        if not self.initialised():
            return False
        if not self.videoLogRunning:
            return False
        print("stopVideoLogRecording")
        ret = self.__api.StopVideoLog()
        print(ret)
        print("StopVideoLog returns: " + str(ret))
        if len(ret) == 0:
            return False
        rc = ret[0][1]
        if rc:
            self.videoLogRunning = False
        return rc

    def convertPILtoStormImageObject(self, pilImageObject):
        stImageObject = self.__api.Imaging.StormTestImageObject(pilImageObject)
        return stImageObject

    def loadSTimageObjectFromFile(self, path):
        stImageObject = self.__api.Imaging.ImageFromFile(path)
        return stImageObject

    def compareIcon(self, iconPath, imagePath, percent, location):
        compareResult = self.__api.CompareIconEx(iconPath, imagePath, percent, location)
        return compareResult

    def getModelTypeNavigator(self):
        if self.navigatorName:
            return self.navigatorName

        print("stormtest.getModelTypeNavigator() epgVersion=%s" % (self.epgVersion))
        navigator = None
        if self.hdServer:
            navigator = "Ethan_HD"
            if self.modelType.LLAMA():
                navigator = "Ethan_TilesUI"
            else:
                v = self.getEpgMajorVersion()
                if v > 1122:
                    navigator = "Ethan_TilesUI"
        else:
            if self.modelType.AMIDALA():
                navigator = "Ethan"

            if self.modelType.Mozart():
                navigator = "Ethan_Mozart"

            if self.modelType.QMS():
                navigator = "Ethan_QMS"

            if self.modelType.XiOne():
                navigator = "Ethan_XiOne"

            if self.modelType.LLAMA():
                navigator = "X3_SD"

        self.navigatorName = navigator
        print("stormtest.getModelTypeNavigator() epgVersion=%s navigator=%s" % (self.epgVersion, navigator))
        return navigator

    def waitImageMatch(self, refImage, percent=80, includedAreas=None, excludedAreas=None, algorithm=None, timeToWait=20, waitGap=0.1):
        if algorithm is None:
            algorithm = self.__api.CompareAlgorithm.Compare1
        return self.__api.WaitImageMatch(refImage=refImage,
                                          percent=percent,
                                          includedAreas=includedAreas,
                                          excludedAreas=excludedAreas,
                                          algorithm=algorithm,
                                          timeToWait=timeToWait,
                                          waitGap=waitGap)

    def waitAudioPresence(self, threshold, timeoutAudioPresence):
        status = self.__api.WaitAudioPresence(threshold, timeoutAudioPresence, self.slotNo)
        return status

    def readImageFromFile(self, imageName):
        # imageName = "myfile.png"
        # returns StormTestImageObject
        status = self.__api.Imaging.StormTestImageObject.FromFile(imageName)
        return status

    def resetSlot(self):
        print("*** resetSlot ***")
        status = self.__api.ResetSlot(self.slotNo)
        return status

    def setSignalRecoveryMode(self):
        rc = self.__api.SetSignalRecoveryMode(self.__api.SignalRecoveryMode.Fast, self.slotNo)
        return rc

    def resyncAudio(self):
        print("*** ResyncAudio ***")
        status = self.__api.ResyncAudio (self.slotNo)
        return status

    def getEpgMajorVersion(self):
        majorVersion = -1
        if self.epgVersion is None:
            return majorVersion
        if "." in self.epgVersion:
            ss = re.sub("\..*$", "", self.epgVersion)
            majorVersion = int(ss)
        print("getEpgMajorVersion: %s %s" % (self.epgVersion, majorVersion))
        return majorVersion

def Main():
    serverIP = "TPS-HS64-1" #or 172.20.116.100

    # serverIP = "tech-hv16-1"
    slotNo = 1
    configServer = "tech-hv16-1"

    try:
        st = EthanStormtestClient()
        st.setStormtestAPI()
        st.connect(slotNo, configServer,serverIP )
        #st.doWork()
    except:
        print("BareBones - Exception")
        tb = traceback.format_exc()
        print(tb)


if __name__ == '__main__':
    Main()
    print("Done")
