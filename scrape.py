from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common import exceptions as EX
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup
from time import sleep
import urllib
import json
    
redirectdriver = webdriver.Firefox()

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

def get_content(link):
    params = urllib.parse.urlencode({ "url": link })
    req = urllib.request.Request("https://mercury.postlight.com/parser?%s"
            % params)
    req.add_header("x-api-key", config['MERCURY_API_KEY'])
    data = json.loads(urllib.request.urlopen(req).read())
    soup = BeautifulSoup(data["content"], "html.parser")
    return soup.get_text()

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

    redirectdriver.get(fblink)
    wait = WebDriverWait(redirectdriver, 5)
    body = driver.find_element_by_tag_name('body')
    try:
        body = wait.until(EC.staleness_of(body))
    except:
        EX.TimeoutException
    url = redirectdriver.current_url
    params = urllib.parse.urlencode({ 
        "apiKey": config['BITLY_API_KEY'],
        "login": config['BITLY_LOGIN'], 
        "longUrl": url
        })
    req = urllib.request.urlopen("http://api.bitly.com/v3/shorten?%s" % params)
    return json.loads(req.read())["data"]["url"]

def get_image(el):
    try:
        return el.find_element_by_css_selector(".mtm img").get_attribute("src")
    except EX.NoSuchElementException:
        pass
    try:
        return el.find_element_by_css_selector(".fbStoryAttachmentImage img").get_attribute("src")
    except EX.NoSuchElementException:
        return False

def get_story(el):
    link = get_link(el)
    ret = {
        "headline": get_headline(el),
        "id": get_id(el),
        "image": get_image(el),
        "deck": get_deck(el),
        "link": link,
        "source": get_source(el),
        "story": link and get_content(link)
    }
    return ret;

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
    
    story_els = []
    stories = []
    while len(stories) < 20:
        sleep(1)
        story_els = driver.find_elements_by_css_selector("[data-testid=fbfeed_story]")
        driver.execute_script("window.scrollTo(0, document.documentElement.scrollTop + window.outerHeight);")
        for el in story_els:
            if get_source(el) not in [x["source"] for x in stories]:
                story = get_story(el)
                stories.append(story)
                print(story)
    with open(user + '.json', 'w') as f:
        f.write(json.dumps(stories))


    driver.close()

redirectdriver.close()
