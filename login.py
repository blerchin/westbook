from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common import exceptions as EX
from selenium.webdriver.common.keys import Keys
import pickle
import re
from os import listdir
from os import path
import os

driver = webdriver.Firefox()
driver.get("http://www.facebook.com");
assert "Facebook - Log In or Sign Up" in driver.title
element = WebDriverWait(driver, 200).until(
    EC.presence_of_element_located((By.CSS_SELECTOR, '.homeSideNav li[data-type="type_user"] a .linkWrap'))
)
files = [int(path.splitext(f)[0]) for f in listdir("cookies")]
files.sort()
num = int(files[-1]) + 1
pickle.dump( driver.get_cookies() , open("cookies/%i.pkl" % num,"wb"))

driver.close()
print("saved credentials :)");
