'''
Created on 18.08.2024

@author: molo01
'''
import time as ti
import traceback
import os
import sys



def load_env():
    with open('C:\Users\PRDA5207\Github_Repos\sky-onbox-e2e-skyq-pa-automation\Storm_test_automation\.env') as f:
        for line in f:
            # Ignore comments and empty lines
            if line.strip() and not line.startswith("#"):
                key, value = line.strip().split("=", 1)
                os.environ[key] = value

# Load the environment variables
# load_env()

# Now you can access them using os.getenv
# my_secret_key = os.getenv('DLL_PATH')
# database_url = os.getenv('PACKAGE')
# stormtest = os.getenv('STORMTEST')


class captureScreenRef:

    def __init__(self, configServer, serverIP, slotNo,api):
        self.__configServer = configServer
        self.__serverIP = serverIP
        self.__slotNo = slotNo

        self.__api = None

        self.__logPath = r"C:\workspace\logs"
        self.__connectStr = "BareBones_py3"
        self.__redratFile = "default"

        if api is None:
            import stormtest.ClientAPI as ClientAPI  # @UnresolvedImport
            self.__api = ClientAPI
        else:
            self.__api = api  # Use the passed API object

    def connect(self):
        import stormtest.ClientAPI as ClientAPI  # @UnresolvedImport
        self.__api = ClientAPI
        self.__api.SetMasterConfigurationServer(self.__configServer)

        self.__api.SetProjectDir(self.__logPath)
        logPath = self.__api.GetLogFileDirectory()
        print("connect: %s" % (logPath))
        ret = self.__api.ConnectToServer(self.__serverIP, self.__connectStr)
        print("ConnectToServer: %s" % (ret))
        ret = self.__api.ReserveSlot(self.__slotNo, self.__redratFile, videoFlag=True)
        print("ReserveSlot: %s" % (ret))
        self.__api.ShowVideo(slotNo=self.__slotNo)

    def release(self):
        self.__api.CloseVideo(self.__slotNo)
        self.__api.FreeSlot(self.__slotNo)
        self.__api.ReleaseServerConnection()

    def do_ResetDefaultParameters(self):
        '''
            Default:
            GetResolution: 720 x 576
            GetFrameRate: 25
            GetMaxBitRate: 2048000

        '''

        ret = self.__api.ResetDefaultParameters(self.__slotNo)
        print("ResetDefaultParameters: %s" % (ret))
        ti.sleep(5)

    def do_CompareImage(self):
        refImage = r"C:\Users\molo01\Pictures\Home_SkyLogo.png"
        testImage = r"C:\workspace\automation_skyde\automated_tests\python3_scripts\basic\xx.png"
        percent = 80

        ret = self.__api.CompareImageEx(refImage, testImage, percent=percent)
        print("CompareImageEx: %s" % (ret))

    def getVideoParams(self):
        '''
            GetResolution: 1280 x 720
            GetFrameRate: 25
            GetMaxBitRate: 394000
        '''

        ret = self.__api.GetResolution(self.__slotNo)
        res = ret
        print("GetResolution: %s" % (ret))
        ret = self.__api.GetFrameRate(self.__slotNo)
        fps = ret
        print("GetFrameRate: %s" % (ret))
        ret = self.__api.GetMaxBitRate(self.__slotNo)
        br = ret
        print("GetMaxBitRate: %s" % (ret))

        videoParamsDict = {}
        videoParamsDict['BitRate'] = br
        videoParamsDict['Resolution'] = res
        videoParamsDict['FrameRate'] = fps
        return videoParamsDict

    def setVideoParams(self):
        '''
            GetResolution: 704 x 576 = 4CIF
            GetFrameRate: 25
            GetMaxBitRate: 256000

        '''
        videoParamsDict = {}
        videoParamsDict['BitRate'] = 1000000
        # 4CIF 1920x1080  1280x720
        videoParamsDict['Resolution'] = "1280x720"
        k = "BitRate"
        v = videoParamsDict[k]
        self.__api.SetMaxBitRate(v, self.__slotNo)
        k = "Resolution"
        v = videoParamsDict[k]
        self.__api.SetResolution(v, self.__slotNo)
        ti.sleep(5)


    def captureScreen(self,image_name_to_save):
            #self.__api.WaitSec(2)
            # Capture the actual screen
            #def CaptureImageEx (rect, filename, jpegQuality=80, overwriteAction=OverWriteAction.NewName, slotNo=0, returnImage=True):
            returnValueArray = self.__api.CaptureImageEx(None, image_name_to_save)
            # Check if capture screen was successful
            # returnValueArray: [SlotNo, Statusflag, StormTestImageObject, saveFileFullPath][16]

            for ret in returnValueArray:
                slot = ret[0]
                statusFlag = ret[1]
                if statusFlag:
                    filename = ret[3]
                else:
                    print("Failure on slot ", slot)
                    return None  # Failure, return None
            if statusFlag:
                print("Captured image is", filename)
                return filename, statusFlag  # Success, return the filename
                # Default, in case of failure or missing status


def human_readable_size(size, decimal_places=2):
    for unit in ['B', 'KB', 'MB', 'GB', 'TB', 'PB']:
        if size < 1024.0 or unit == 'PB':
            break
        size /= 1024.0
    # return f"{size:.{decimal_places}f}{unit}"


def Main():
    serverIP = "TPS-HS64-1"
    # serverIP = "tech-hv16-1"
    slotNo = 10
    configServer = "tech-hv16-1"
    image_name_to_save="C:\Users\PRDA5207\Github_Repos\sky-onbox-e2e-skyq-pa-automation\Storm_test_automation\Captured_ref_images\complete_scan.bmp"
    try:
        st = captureScreenRef(configServer, serverIP, slotNo, None)
        st.connect()
        st.captureScreen(image_name_to_save)
    except:
        print("BareBones - Exception")
        tb = traceback.format_exc()
        print(tb)
    finally:
        st.release()


if __name__ == '__main__':
    Main()
    print("Done")

#C:\tools\Python27\python.exe C:\Users\PRDA5207\Github_Repos\sky-onbox-e2e-skyq-pa-automation\Storm_test_automation\bareBoneStorm2.py