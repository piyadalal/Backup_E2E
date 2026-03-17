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


class Run:

    def __init__(self, configServer, serverIP, slotNo,api):
        self.__configServer = configServer
        self.__serverIP = serverIP
        self.__slotNo = slotNo

        self.__api = None

        if api is None:
            import stormtest.ClientAPI as ClientAPI  # @UnresolvedImport
            self.__api = ClientAPI
        else:
            self.__api = api  # Use the passed API object

        self.__logPath = r"C:\workspace\logs"
        self.__connectStr = "BareBones_py3"
        self.__redratFile = "default"

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

    def Start_scan(self):
        ret = self.__api.PressButton("Home")
        ti.sleep(3)
        #OK, right, OK , OK , OK , RIGHT; OK
        for i in range(0,10):
            ret = self.__api.PressButton("Down")
            ti.sleep(1)
        ret = self.__api.PressButton("Right")
        ti.sleep(1)
        ret = self.__api.PressDigits("0")
        ti.sleep(1)
        ret = self.__api.PressDigits("0")
        ti.sleep(1)
        ret = self.__api.PressDigits("0")
        ti.sleep(1)
        ret = self.__api.PressDigits("1")
        ti.sleep(1)
        ret = self.__api.PressButton("Ok")
        for i in range(0, 3):
            ret = self.__api.PressButton("Down")
            ti.sleep(1)
        ret = self.__api.PressButton("Right")
        ti.sleep(1)
        ret = self.__api.PressButton("Ok")
        ti.sleep(1)
        ret = self.__api.PressButton("Left")
        ti.sleep(1)
        ret = self.__api.PressButton("Ok")
        '''
         ret = self.__api.PressButton("Home")
        ti.sleep(3)
        ret = self.__api.PressButton("Ok")
        ti.sleep(3)
        ret = self.__api.PressButton("Ok")
        ti.sleep(3)
        ret = self.__api.PressButton("Right")
        ti.sleep(3)
        ret = self.__api.PressButton("Ok")
        ti.sleep(3)
        ret = self.__api.PressButton("Ok")
        ti.sleep(3)
        ret = self.__api.PressButton("Right")
        ti.sleep(3)
        ret = self.__api.PressButton("Ok")
        ti.sleep(3)
        ret = self.__api.PressButton("Ok")
        ti.sleep(3)
        ret = self.__api.PressButton("Ok")
        ti.sleep(3)
        '''



def Main():

    serverIP = "TPS-HS64-1"
    # serverIP = "tech-hv16-1"
    slotNo = 10
    configServer = "tech-hv16-1"
    #image_to_be_checked = "C:\Users\PRDA5207\Github_Repos\sky-onbox-e2e-skyq-pa-automation\Storm_test_automation\Captured_ref_images\start_scan.bmp"
    try:
        st = Run(configServer, serverIP, slotNo,None)
        st.connect()
        st.Start_scan()
        #matched = st.is_scanStartScreen(image_to_be_checked)
        #st.scan_start()
        #st.PINprompt()
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
#ToDo: OCR reading from scanned channels, matching across all boxes and matching within range, if +-8 of range a transponder is missing, tunning to services from each transponder