from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common import exceptions as EX
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup
import time
import urllib
import json
import re
import os

with open(".config") as f:
    config = json.loads(f.read())

users = {}
with open(".credentials") as f:
    creds = f.readlines()
    for l in creds:
        cred = l.strip().split(":")
        users[cred[0]] = cred[1]

def get_source(el):
    try:
        tag = el.find_element_by_tag_name("h5")
        text = ""
        for e in tag.find_elements_by_xpath("./*/*"):
            text += e.text;
        return text
    except EX.NoSuchElementException:
        return False

def get_deck(el):
    try:
        return el.find_element_by_tag_name("p").text
    except EX.NoSuchElementException:
        return False

def get_headline(el):
    try:
        return el.find_element_by_css_selector(".mbs a").text
    except EX.NoSuchElementException:
        return False

def get_article(link):
    params = urllib.parse.urlencode({ "url": link })
    req = urllib.request.Request("https://mercury.postlight.com/parser?%s"
            % params)
    req.add_header("x-api-key", config['MERCURY_API_KEY'])
    try:
        data = json.loads(urllib.request.urlopen(req).read())
    except urllib.error.HTTPError:
        return False
    soup = BeautifulSoup(data["content"], "html.parser")
    content = soup.get_text().strip()
    content = re.sub(r'\n\s*\n', r'\r', content,flags=re.M)
    return content

def get_id(el):
    return el.get_attribute("id")

def get_link(el):
    fblink = False
    try:
        link = el.find_element_by_css_selector(".mtm a").get_attribute("href")
        if link[0] == "/":
            fblink = "https://facebook.com" + link
        else:
            fblink = link
    except EX.NoSuchElementException:
        return False

    return fblink

def resolve_link(fblink, driver):
    try:
        body = driver.find_element_by_tag_name('body')
        driver.get(fblink)
        wait = WebDriverWait(driver, 5)
        body = wait.until(EC.staleness_of(body))
    except Exception as e:
        print(e)
    url = driver.current_url
    params = urllib.parse.urlencode({
        "apiKey": config['BITLY_API_KEY'],
        "login": config['BITLY_LOGIN'],
        "longUrl": url
        })
    req = urllib.request.urlopen("http://api.bitly.com/v3/shorten?%s" % params)
    return json.loads(req.read())["data"]["url"]

def get_image(el):
    try:
        src = el.find_element_by_css_selector(".mtm img").get_attribute("src")
        loc = "%s/img/%s.jpg" % (os.getcwd(), time.time())
        urllib.request.urlretrieve(src, loc)
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
        "source": get_source(el)
    }
    return ret;

driver = False;
def get_content(story):
    link = resolve_link(story['link'], driver)
    print(link)
    story['link'] = link
    story['story'] = link and get_article(link)
    return story

for user, password in users.items():
    driver = webdriver.Firefox()
    driver.get("http://www.facebook.com");
    assert "Facebook" in driver.title
    email_field = driver.find_element_by_name("email")
    email_field.clear()
    email_field.send_keys(user)
    password_field = driver.find_element_by_name("pass")
    password_field.send_keys(password)
    password_field.send_keys(Keys.RETURN)
    print("logged in");

    story_els = []
    stories = []
    while len(stories) < 50:
        time.sleep(1)
        story_els = driver.find_elements_by_css_selector("[data-testid=fbfeed_story]")
        driver.execute_script("window.scrollTo(0, document.documentElement.scrollTop + window.outerHeight);")
        for el in story_els:
            if get_id(el) not in [x["id"] for x in stories]:
                print("new story")
                story = get_story(el)
                stories.append(story)
                print(story)
    stories = list(map(get_content, stories))

    fname = re.sub('[^a-zA-Z0-9 \n\.]', '_', user)
    with open(fname + '.json', 'w') as f:
        f.write(json.dumps(stories))


    driver.close()
