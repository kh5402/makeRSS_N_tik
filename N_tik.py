from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from datetime import datetime
import pytz
import xml.etree.ElementTree as ET
import requests
import os
from xml.dom import minidom

webhook_url = os.environ.get('DISCORD_WEBHOOK')
xml_file = 'N_tik.xml'

japan_tz = pytz.timezone('Asia/Tokyo')
current_time = datetime.now(japan_tz).strftime('%Y-%m-%d %H:%M:%S')

options = webdriver.ChromeOptions()
options.add_argument("--headless")
options.add_argument('--no-sandbox')
options.add_argument('--disable-setuid-sandbox')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--disable-accelerated-2d-canvas')
options.add_argument('--disable-gpu')
options.binary_location = "/usr/bin/chromium-browser"

driver = webdriver.Chrome(options=options)

try:
    tree = ET.parse(xml_file)
    root = tree.getroot()
    channel = root.find('channel')
except FileNotFoundError:
    root = ET.Element("rss", version="2.0")
    channel = ET.SubElement(root, "channel")
    ET.SubElement(channel, "title").text = "乃木坂 TikTok Videos"
    ET.SubElement(channel, "link").text = "https://www.tiktok.com/"
    ET.SubElement(channel, "description").text = "Latest TikTok videos"

existing_titles = set()
for item in channel.findall('item'):
    title = item.find('title').text
    existing_titles.add(title)
print(existing_titles) 

discord_notify = []

driver.get("https://www.tiktok.com/@nogizaka46_official?lang=jp")
WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, 'body')))
wait = WebDriverWait(driver, 20)
wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, "tiktok-x6y88p-DivItemContainerV2")))

# 3回スクロールして出てくる動画を取得
for _ in range(3):
    driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.END)
    time.sleep(2)

div_containers = driver.find_elements(By.CLASS_NAME, "tiktok-x6y88p-DivItemContainerV2")
#print(div_containers)
#print(enumerate(reversed(div_containers)))

for i, div_container in enumerate(reversed(div_containers)):
    try:
        video_desc = div_container.find_element(By.CLASS_NAME, "tiktok-16ou6xi-DivTagCardDesc").text        
        video_date = current_time
        video_url = div_container.find_element(By.CLASS_NAME, "tiktok-1wrhn5c-AMetaCaptionLine").get_attribute('href')

        #print(video_desc)
        
        if video_desc not in existing_titles:
            discord_notify.append({
                'title': video_desc,
                'url': video_url,
                'date': video_date,
            })

            item_elem = ET.SubElement(channel, "item")
            ET.SubElement(item_elem, "title").text = video_desc
            ET.SubElement(item_elem, "url").text = video_url
            ET.SubElement(item_elem, "date").text = video_date
            
    except Exception as e:
        print(f"動画{i+1}でエラー: {e}")

print('#discord_notify' + str(discord_notify))

for video in discord_notify:
    data = {
        "content": f"新しい動画があるよ！\n日付: {video['date']}\nタイトル: {video['title']}\nURL: {video['url']}\n"
    }
    requests.post(webhook_url, data=data)

# XMLファイルを保存（エンコーディングをUTF-8に設定、改行も入れる）
tree = ET.ElementTree(root)
xml_str = ET.tostring(root, encoding='utf-8', method='xml')

# minidomできれいにフォーマットする
dom = minidom.parseString(xml_str)
pretty_xml_str = dom.toprettyxml(indent="  ")

# 空白行を取り除く
pretty_xml_str = os.linesep.join([s for s in pretty_xml_str.splitlines() if s.strip()])

with open(xml_file, 'w', encoding='utf-8') as f:
    f.write(pretty_xml_str)

driver.quit()


