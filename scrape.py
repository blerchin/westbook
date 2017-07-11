from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common import exceptions as EX
from selenium.webdriver.common.keys import Keys
from time import sleep
import csv

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

def get_lede(el):
    try:
        return el.find_element_by_tag_name("p").text
    except EX.NoSuchElementException:
        return False

def get_headline(el):
    try:
        return el.find_element_by_css_selector(".mbs a").text
    except EX.NoSuchElementException:
        return False

def get_id(el):
    return el.get_attribute("id")

def get_link(el):
    try:
        link = el.find_element_by_css_selector(".mtm a").get_attribute("href")
        if link[0] == "/":
            return "https://facebook.com" + link
        else:
            return link
    except EX.NoSuchElementException:
        return False
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
    ret = {
        "headline": get_headline(el),
        "id": get_id(el),
        "image": get_image(el),
        "lede": get_lede(el),
        "link": get_link(el),
        "source": get_source(el)
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
            story = get_story(el)
            if story["source"] not in [x["source"] for x in stories]:
                stories.append(story)
                print(story)
    with open(user + '.csv', 'w') as f:
        writer = csv.DictWriter(f, stories[0].keys())
        writer.writeheader()
        for story in stories:
            writer.writerow(story)

driver.close()



