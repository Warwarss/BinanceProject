import os
import mouse
import time
import config
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
# http://api.whatsapp.com/send?phone=xxxxxxxxxx yabancı numaralarla konuşabilmek için bunu kullan

global driver
global wait5

class Person:
    def __init__(self,name):
        self.name=name
    status=False 

def open_chat (name):    
        chat_value=f'//span[@title="{name}"]'
        wait5.until(EC.presence_of_element_located((By.XPATH,'//div[@contenteditable="true"][@data-tab="3"]'))).click
        search_box=driver.find_element(by=By.XPATH, value='//div[@contenteditable="true"][@data-tab="3"]')
        search_box.clear()
        search_box.click()
        search_box.send_keys(name)       
        wait5.until(EC.presence_of_element_located((By.XPATH,chat_value)))
        chat=driver.find_element(by=By.XPATH, value=chat_value)
        chat.click()
        try:
            status=driver.find_element(by=By.XPATH, value='//span[@title="online"]')
        except:
            #print(f"{name} is not online", current_time )
            if (person.status==True):
                person.status=False
                now = datetime.now()
                current_time = now.strftime("%H:%M:%S")
                print(f"{name} went offline at", current_time )
        else:
            #print(f"{name} is online", current_time )
            if (person.status==False):
                person.status=True
                now = datetime.now()
                current_time = now.strftime("%H:%M:%S")
                print(f"{name} came online at", current_time)

PATH="C:\Program Files (x86)\Chromedriver\chromedriver.exe"
options = webdriver.ChromeOptions()
options.add_argument(r"--user-data-dir=C:\Users\ACER\AppData\Local\Google\Chrome\User Data")
options.add_argument(r"--profile--directory=C:\Users\ACER\AppData\Local\Google\Chrome\User Data\Profile 1")
driver = webdriver.Chrome(PATH,chrome_options=options)
wait5=WebDriverWait(driver, 5)
driver.get("https://web.whatsapp.com")
time.sleep(10)
Array=config.Array
for name in Array:
    person=Person(name)
while(1):
    for name in Array:
        open_chat(name)   
