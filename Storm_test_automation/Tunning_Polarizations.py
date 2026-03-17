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


class BareBones:

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

    def video_params(self):
        print("getting video quality: ")
        ti.sleep(5)

        videoParamsDict = self.getVideoParams()
        print(videoParamsDict)
        s2 = human_readable_size(videoParamsDict["BitRate"]).replace("B", "")
        s = "(%s),%s" % (videoParamsDict["Resolution"], s2)
        print("VideoSetting=%s" % (s))

    def Tune(self):
        self.__api.PressButton("Home")
        ti.sleep(1)
        self.__api.PressButton("Back")
        ti.sleep(1)
        self.__api.PressButton("Back")
        ti.sleep(2)
        self.__api.PressDigits("3")
        ti.sleep(1)
        self.__api.PressDigits("0")
        ti.sleep(1)
        self.__api.PressDigits("1")
        ti.sleep(5)
        #self.__api.PressButton("Ok")
        #ti.sleep(2)
        # check if PIN prompt asked
        #take PIN input from user
        #if already on 300?
        self.__api.PressDigits("0")
        ti.sleep(2)
        self.__api.PressDigits("8")
        ti.sleep(2)
        self.__api.PressDigits("1")
        ti.sleep(2)
        self.__api.PressDigits("5")
        ti.sleep(2)
        self.__api.PressButton("Ok")
        ti.sleep(2)




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
    #image_to_be_checked = "C:\Users\PRDA5207\Github_Repos\sky-onbox-e2e-skyq-pa-automation\Storm_test_automation\Captured_ref_images\start_scan.bmp"
    try:
        st = BareBones(configServer, serverIP, slotNo,None)
        st.connect()
        st.Tune()
        st.video_params()
        #st.Reset()
        #matched = st.is_scanStartScreen(image_to_be_checked)
        #st.scan_start()
        #st.PINprompt()
    except:
        print("BareBones - Exception")
        tb = traceback.format_exc()
        print(tb)

    finally:
        st.release()

'''
                if st.is_scanStartScreen():
            st.scan_start()
        else:
            st.Reset()
            matched = st.is_scanStartScreen()
            if matched:
                st.scan_start()
            else:
                return None

    except:
        print("BareBones - Exception")
        tb = traceback.format_exc()
        print(tb)
    '''



def Main__():
    serverIP = "TPS-HS64-1"
    # serverIP = "tech-hv16-1"
    slotNo = 10
    configServer = "tech-hv16-1"
    try:
        st = BareBones(configServer, serverIP, slotNo,None)
        st.connect()
        #image_to_be_checked = "C:\Users\PRDA5207\Github_Repos\sky-onbox-e2e-skyq-pa-automation\Storm_test_automation\Captured_ref_images\start_scan.bmp"
        #st.scan_start()
        #st.is_scanStartScreen(image_to_be_checked)
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
