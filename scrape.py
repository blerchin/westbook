from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common import exceptions as EX
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup
from wand.image import Image
import pickle
import logging
import time
import urllib
import ssl
import json
import re
import os
import sys

ssl._create_default_https_context = ssl._create_unverified_context

def get_author(el):
    try:
        text = el.find_element_by_tag_name(".FPmhX").text
        return text
    except EX.NoSuchElementException as e:
        return False

def get_headline(el):
    try:
        return el.find_element_by_css_selector(".C4VMK span span").text
    except EX.NoSuchElementException:
        return False

def download_img(url):
    loc = "%s/img/%s.jpg" % (os.getcwd(), time.time())
    urllib.request.urlretrieve(url, loc)
    with Image(filename=loc) as img:
        img.save(filename=loc)
    return loc


def get_image(el):
    try:
        src = el.find_element_by_css_selector("._97aPb img").get_attribute("src")
        if src:
            return download_img(src)
    except EX.NoSuchElementException:
        return False
    return False

def get_story(el):
    ret = {
        "headline": get_headline(el),
        "image": get_image(el),
        "user": get_author(el),
    }
    return ret;

def scrape_user():
    driver = webdriver.Firefox()
    driver.get("https://www.instagram.com/accounts/login/");
    element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "gmFkV")))
    element = driver.find_element_by_css_selector('.gmFkV')
    username = element.text
    print("%s logged in" % username);

    story_els = []
    stories = []
    headlines = []
    failures = 0
    selector = "data-insertion-position"

    while len(stories) < 30 and failures < 100:
        time.sleep(1)
        try:
            el = driver.find_element_by_css_selector('article')
            if get_headline(el) not in headlines:
                story = get_story(el)
                stories.append(story)
                headlines.append(story['headline'])
                print(story['user'])
                failures = 0
            else:
                driver.execute_script("window.scrollTo(0, document.documentElement.scrollTop + window.outerHeight/2);")
        except EX.NoSuchElementException as e:
            print(e)
            failures += 1
            if(failures > 10):
                break;
            print('retry %i' % failures)
            continue

    with open( "data/%s.json" % username, 'w') as f:
        f.write(json.dumps({ 'username': username, 'stories': stories }))

    driver.close()

scrape_user()
