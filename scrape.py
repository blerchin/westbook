from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common import exceptions as EX
from selenium.webdriver.common.keys import Keys
from multiprocessing import Pool
from bs4 import BeautifulSoup
from wand.image import Image
import pickle
import logging
import time
import urllib
import json
import re
import os
import sys

with open(".config") as f:
    config = json.loads(f.read())

def get_source(el):
    try:
        tag = el.find_element_by_tag_name("h5")
        text = ""
        for e in tag.find_elements_by_xpath("./*/*"):
            text += e.text;
        return text
    except EX.NoSuchElementException as e:
        return False

def get_deck(el):
    try:
        deck = ""
        grafs = el.find_elements_by_tag_name("p")
        for graf in grafs:
            deck += graf.text
        return deck;
    except EX.NoSuchElementException:
        return False

def get_headline(el):
    try:
        return el.find_element_by_css_selector(".mbs a").text
    except EX.NoSuchElementException:
        return False

def get_article(link):
    print("parsing %s" % link)
    if("facebook.com" in link):
        return
    params = urllib.parse.urlencode({ "url": link })
    req = urllib.request.Request("https://mercury.postlight.com/parser?%s"
            % params)
    req.add_header("x-api-key", config['MERCURY_API_KEY'])
    data = json.loads(urllib.request.urlopen(req).read())
    soup = BeautifulSoup(data["content"], "html.parser")
    content = ""
    for string in soup.stripped_strings:
        content += string + "\r";
    data['content'] = content.strip()
    print(data['content'])
    return data;

def get_id(el):
    return el.get_attribute("id")

def get_link(el):
    fblink = ''
    try:
        link = el.find_element_by_css_selector(".mtm a").get_attribute("href")
        if link[0] == "/":
            fblink = "https://facebook.com" + link
        else:
            fblink = link
    except EX.NoSuchElementException:
        return False

    return fblink

def resolve_link(story):
    link = story['link']
    if(link and len(link) > 0):
        print("resolving %s" % link)
        args = urllib.parse.parse_qs(urllib.parse.urlparse(link).query)
        if "u" in args:
            url = args['u'][0]
            story['orig_link'] = url
            params = urllib.parse.urlencode({
                "apiKey": config['BITLY_API_KEY'],
                "login": config['BITLY_LOGIN'],
                "longUrl": url
                })
            req = urllib.request.urlopen("http://api.bitly.com/v3/shorten?%s" % params)
            story['link'] = json.loads(req.read())["data"]["url"]

def get_image(el):
    try:
        src = el.find_element_by_css_selector(".mtm img").get_attribute("src")
        loc = "%s/img/%s.jpg" % (os.getcwd(), time.time())
        urllib.request.urlretrieve(src, loc)
        with Image(filename=loc) as img:
            img.type = "grayscale"
            img.gamma(1.7)
            img.save(filename=loc)
        return loc
    except EX.NoSuchElementException:
        pass
    try:
        return el.find_element_by_css_selector(".fbStoryAttachmentImage img").get_attribute("src")
    except EX.NoSuchElementException:
        return False

def get_story(el):
    ret = {
        "headline": get_headline(el),
        "id": get_id(el),
        "image": get_image(el),
        "deck": get_deck(el),
        "link": get_link(el),
        "orig_link": False,
        "source": get_source(el),
    }
    return ret;

def get_content(story):
    try:
        resolve_link(story)
        if(story['orig_link']):
            article = get_article(story['orig_link'])
            story['story'] =  article and article['content']
        return story
    except Exception as e:
        logging.exception(e)

def scrape_user(user_num):
    driver = webdriver.Firefox()
    driver.get("http://www.facebook.com");
    cookies = pickle.load(open("cookies/%i.pkl" % user_num, "rb"))
    for cookie in cookies:
        driver.add_cookie(cookie)
    driver.refresh()
    element = WebDriverWait(driver, 10).until(EC.title_is("Facebook"))
    element = driver.find_element_by_css_selector('.homeSideNav li[data-type="type_user"] a .linkWrap')
    fullname = element.text
    print("%s logged in" % fullname);

    story_els = []
    stories = []
    failures = 0
    selector = "data-insertion-position"
    try:
        last_pos = int(driver.find_element_by_css_selector('[aria-posinset]').get_attribute('aria-posinset')) + 1
        selector = "aria-posinset"
    except EX.NoSuchElementException:
        last_pos = int(driver.find_element_by_css_selector('[%s]' % selector).get_attribute(selector)) + 1

    while len(stories) < 100 and failures < 100:
        time.sleep(1)
        try:
            el = driver.find_element_by_css_selector('[%s="%i"]' % (selector, last_pos + 1))
            story = get_story(el)
            stories.append(story)
            print(last_pos + 1)
            print(story['source'])
            last_pos += 1
            failures = 0
        except EX.NoSuchElementException as e:
            print(e)
            failures += 1
            if(failures > 10):
                selector = "data-insertion-position"
            print('retry %i' % failures)
            driver.execute_script("window.scrollTo(0, document.documentElement.scrollTop + window.outerHeight/2);")
            continue

    stories = list(map(get_content, stories))

    with open( "data/%i.json" % user_num, 'w') as f:
        f.write(json.dumps({ 'fullname': fullname, 'stories': stories }))

    driver.close()

if(len(sys.argv) > 1):
    scrape_user(int(sys.argv[1]))
else:
    with Pool(5) as p:
        users = [int(os.path.splitext(os.path.basename(f))[0]) for f in os.listdir("cookies")]
        p.map(scrape_user, users)
