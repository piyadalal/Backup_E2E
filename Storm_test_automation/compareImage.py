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


class compareImage:

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


    def do_compare(self, ref_image, captured_image):
        print('entered do comapre')
        refImageResource = 'C:\Users\PRDA5207\Github_Repos\sky-onbox-e2e-skyq-pa-automation\Storm_test_automation\Captured_ref_images'
        # Region to check for when comparing images
        # Image to check for
        #image_file_obj = open(img_CompScreen, "rb").read()
        #self.__api.WriteNamedImage(img_CompScreen, (image_file_obj, 200, 200))
        # Return value flag
        returnValueArray = self.__api.CompareImageEx(ref_image, captured_image)
        # returnValueArray = StormTest.WaitImageMatch (
        # for ret in returnValueArray:
        #     statusFlag = ret[1]
        # slot = ret[0]
        # if statusFlag == False:
        # # Image does not match reference
        #     print "Image does not match reference on slot", slot
        # saveStatus = ret[2].Save("cap_resImage.png")
        # if saveStatus:
        #     print "A screen capture has been saved"
        #     return statusFlag
        if returnValueArray:
            print('Images Matched')
        else:
            print('Images not matched')
        return returnValueArray




def human_readable_size(size, decimal_places=2):
    for unit in ['B', 'KB', 'MB', 'GB', 'TB', 'PB']:
        if size < 1024.0 or unit == 'PB':
            break
        size /= 1024.0
    # return f"{size:.{decimal_places}f}{unit}"


def Main():
    serverIP = "TPS-HS64-1"
    # serverIP = "tech-hv16-1"
    slotNo = 11
    configServer = "tech-hv16-1"
    image_CompScreen = "C:\Users\PRDA5207\Github_Repos\sky-onbox-e2e-skyq-pa-automation\Storm_test_automation\Captured_ref_images\start_scan.bmp"

    try:
        st = compareImage(configServer, serverIP, slotNo)
        st.connect()
        st.do_compare(image_CompScreen)
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