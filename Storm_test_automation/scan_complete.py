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


class Scan_complete:

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

    def do_CompareImage(self):
        refImage = r"C:\Users\molo01\Pictures\Home_SkyLogo.png"
        testImage = r"C:\workspace\automation_skyde\automated_tests\python3_scripts\basic\xx.png"
        percent = 80

        ret = self.__api.CompareImageEx(refImage, testImage, percent=percent)
        print("CompareImageEx: %s" % (ret))


    def is_scanStartScreen(self,image_to_be_checked):

        from captureScreenRef import captureScreenRef
        from compareImage import compareImage
        capture_screen_ref = captureScreenRef(self.__configServer, self.__serverIP, self.__slotNo, None)
        #capture_screen_ref.connect()
        # Initialize the image comparison object
        compare_image_obj = compareImage(self.__configServer, self.__serverIP, self.__slotNo, None)

        # Start an infinite loop to keep capturing and comparing until a match is found
        matched = False
        print(matched)
        while not matched:
            self.__api.PressButton("Home")
            # Capture the screen and check if the capture was successful
            [captured_image, state] = capture_screen_ref.captureScreen("C:\Users\PRDA5207\Github_Repos\sky-onbox-e2e-skyq-pa-automation\Storm_test_automation\Captured_ref_images\captured_screen")
            print(captured_image)
            if state:
                #print("Captured screen location: {%s}".format(captured_image))
                # Optionally store the captured image location in a variable
                image_location = captured_image
            else:
                print("Image not stored")

            res = self.__api.CaptureImageEx(None, None)
            slot,res,image,filename = res[0]
            image.Save("C:\Users\PRDA5207\Github_Repos\sky-onbox-e2e-skyq-pa-automation\Storm_test_automation\Captured_ref_images\captured_screen.png")
            #captured = self.__api.CaptureImageEx(filename)
            matched = self.__api.CompareImageEx(image, image_to_be_checked)
            if matched:
                print('Images Matched')
            # Compare the captured image with the reference image
            #matched = compare_image_obj.do_compare(captured_image,image_to_be_checked)

            # If the images don't match, wait for 10 seconds, press "Home" and try again
            if not matched:
                print("No match found, retrying...")
                 # Press "Home"
                ti.sleep(60)  # Wait for 10 seconds before retrying

        # Once a match is found, return the result
        return matched



    # OK, OK, PIN entry , PIN entry 2 times, OK, two times down, OK,OK

    def scanCompleted(self):
        from captureScreenRef import captureScreenRef
        #scan_complete_screen = "C:\Users\PRDA5207\Github_Repos\sky-onbox-e2e-skyq-pa-automation\Storm_test_automation\Ref_images\complete_scan.bmp"
        #ti.sleep(120) # to see if necessary
        #self.is_scanStartScreen(scan_complete_screen)

        ti.sleep(1)
        ret = self.__api.PressDigits("0")
        ti.sleep(1)
        ret = self.__api.PressDigits("8")
        ti.sleep(1)
        ret = self.__api.PressDigits("1")
        ti.sleep(1)
        ret = self.__api.PressDigits("5")
        ti.sleep(2)
        ret = self.__api.PressDigits("0")
        ti.sleep(1)
        ret = self.__api.PressDigits("8")
        ti.sleep(1)
        ret = self.__api.PressDigits("1")
        ti.sleep(1)
        ret = self.__api.PressDigits("5")
        ti.sleep(2)
        self.__api.PressButton('Ok')
        ti.sleep(1)
        self.__api.PressButton('Down')
        ti.sleep(1)
        self.__api.PressButton('Down')
        ti.sleep(1)
        self.__api.PressButton('Ok')
        ti.sleep(1)
        self.__api.PressButton('Ok')
        ti.sleep(1)





def Main():

    serverIP = "TPS-HS64-1"
    # serverIP = "tech-hv16-1"
    slotNo = 10
    configServer = "tech-hv16-1"
    #image_to_be_checked = "C:\Users\PRDA5207\Github_Repos\sky-onbox-e2e-skyq-pa-automation\Storm_test_automation\Captured_ref_images\start_scan.bmp"
    try:
        st = Scan_complete(configServer, serverIP, slotNo,None)
        st.connect()
        st.scanCompleted()
        #matched = st.is_scanStartScreen(image_to_be_checked)
        #st.scan_start()
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