'''
Created on 4 Feb 2022

@author: remotedesktop
'''
import selenium
from selenium import webdriver
from pprint import pprint
from selenium.webdriver.common.keys import Keys
import traceback
import time


class SeleniumControlStream1:
    '''
    '''

    def __init__(self):
        self.seleniumRemote = False
        # Windows PC
        self.IP = "127.0.0.1"
        # self.chromeDriver = r"C:\Selenium\chromedriver_win32\chromedriver.exe"
        self.chromeDriver = "C:\Users\SKYDE-E2E-TOOL\Downloads\Router_Interops_local\Router_Interops\selenium\chromedriver.exe"
        # self.chromeEXE = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
        self.chromeEXE = "C:\Program Files\Google\Chrome\Application\chrome.exe"

class RTAX55:
    def __init__(self):
        # declare something
        self.url = None

    def doWork(self):
        # Set the path to the downloaded ChromeDriver executable
        # System.setProperty("webdriver.chrome.driver", "/path/to/chromedriver")
        # WebDriver driver = new ChromeDriver()

        # capabilities['javascriptEnabled'] = True
        # capabilities['resolution'] = "1920x1080"

        options = webdriver.ChromeOptions()

        options.add_argument("--disable-extensions")
        options.add_argument("--disable-notifications")
        options.add_argument("--ignore-certificate-errors")
        options.add_experimental_option("detach", True)
        options.add_argument("--disable-search-engine-choice-screen")

        options.binary_location = 'C:\Program Files\Google\Chrome\Application\chrome.exe'

        driver = webdriver.Chrome(executable_path='C:\Users\SKYDE-E2E-TOOL\Downloads\chromedriver-win64\chromedriver-win64\chromedriver.exe', options=options)

        # options = webdriver.ChromeOptions()
        # options.add_argument("--headless=new")
        #
        # Create a new instance of the Chrome browser
        # driver = webdriver.Chrome(options=options)

        # Open link target and get the page content
        driver.get('http://www.asusrouter.com/Main_Login.asp')
        time.sleep(2)
        # driver.get('192.168.50.1')
        content = driver.page_source

        elem = driver.find_elements_by_id("login_username")
        elem[0].send_keys("admin")

        elem = driver.find_elements_by_name("login_passwd")
        elem[0].send_keys("Multifeed1")

        elem[0].send_keys(Keys.ENTER)
        time.sleep(5)

        elem = driver.find_elements_by_id("Advanced_OperationMode_Content_menu")
        elem[0].click()
        time.sleep(1)

        elem = driver.find_elements_by_id("Advanced_SettingBackup_Content_tab")
        elem[0].click()
        time.sleep(1)

        elem = driver.find_elements_by_name("file")
        elem[0].send_keys("C:\Users\SKYDE-E2E-TOOL\Downloads\AX55_both_WPA2_AES.CFG")



if __name__ == '__main__':
    rt = RTAX55()
    rt.doWork()
    # Main2()
    print "Done"
