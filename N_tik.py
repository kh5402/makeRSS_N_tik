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

# 日本のタイムゾーンを設定
japan_tz = pytz.timezone('Asia/Tokyo')

# 現在の日時を日本時間で取得
current_time = datetime.now(japan_tz).strftime('%Y-%m-%d %H:%M:%S')

options = webdriver.ChromeOptions()
options.add_argument("--headless")  # ヘッドレスモード
options.add_argument('--no-sandbox')
options.add_argument('--disable-setuid-sandbox')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--disable-accelerated-2d-canvas')
options.add_argument('--disable-gpu')
options.binary_location = "/usr/bin/chromium-browser"  # Chromiumのパスを指定

driver = webdriver.Chrome(options=options)


# XML（RSS）の基本構造を作成
root = ET.Element("rss", version="2.0")
channel = ET.SubElement(root, "channel")
ET.SubElement(channel, "title").text = "TikTok Videos"
ET.SubElement(channel, "link").text = "https://www.tiktok.com/"
ET.SubElement(channel, "description").text = "Latest TikTok videos"

# TikTokのページにアクセス
driver.get("https://www.tiktok.com/@nogizaka46_official?lang=jp")

# ページがちゃんとロードされるまで待つ
WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, 'body')))
wait = WebDriverWait(driver, 10)
wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, "tiktok-x6y88p-DivItemContainerV2")))

for _ in range(3):
    driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.END)
    time.sleep(2)

div_containers = driver.find_elements(By.CLASS_NAME, "tiktok-x6y88p-DivItemContainerV2")

# 既存のタイトルをセットに保存
existing_titles = set()
tree = ET.parse('N_tik.xml')
root = tree.getroot()
for video in root.findall('video'):
    title = video.find('title').text
    existing_titles.add(title)

# Discordに送る新しい動画のリスト
discord_notify = []

for i, div_container in enumerate(div_containers):
    try:
        # find_element_by_class_nameを使う前に、div_containerが何か確認する
        print(f"div_container {i+1}: {div_container.text}")

        video_views = div_container.find_element(By.CLASS_NAME, "video-count").text
        video_desc = div_container.find_element(By.CLASS_NAME, "tiktok-16ou6xi-DivTagCardDesc").text        
        video_date = current_time
        video_url = div_container.find_element(By.CLASS_NAME, "tiktok-1wrhn5c-AMetaCaptionLine").get_attribute('href')

        if video_desc not in existing_titles:
            discord_notify.append({
                'title': video_desc,
                'url': video_url,
                'date': video_date,
                'views': video_views
            })

            # XMLに新しい動画の情報を追加
            video_elem = ET.SubElement(channel, "video")
            ET.SubElement(video_elem, "title").text = video_desc
            ET.SubElement(video_elem, "url").text = video_url
            ET.SubElement(video_elem, "date").text = video_date
            ET.SubElement(video_elem, "views").text = video_views
            
    except Exception as e:
        print(f"動画{i+1}でエラー: {e}")
        
# Discord Webhookを使って通知
webhook_url = "your_discord_webhook_url_here"
for video in discord_notify:
    data = {
        "content": f"新しい動画があります！\nタイトル: {video['title']}\nURL: {video['url']}\n日付: {video['date']}\n視聴回数: {video['views']}"
    }
    requests.post(webhook_url, data=data)

# XMLファイルを保存
tree = ET.ElementTree(root)
tree.write("N_tik.xml")

driver.quit()
