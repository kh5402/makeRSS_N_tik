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
# User-Agentを最新のものに設定
options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36") 

# Headlessモードを無効にする場合は、以下の行をコメントアウト
options.add_argument("--headless") 

options.add_argument('--no-sandbox')
options.add_argument('--disable-setuid-sandbox')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--disable-accelerated-2d-canvas')
options.add_argument('--disable-gpu')
options.binary_location = "/usr/bin/chromium-browser"

driver = webdriver.Chrome(options=options)

print("----- XML 読み込み開始 -----") 
try:
    tree = ET.parse(xml_file)
    root = tree.getroot()
    channel = root.find('channel')
    print("XML ファイルを読み込みました。") 
except FileNotFoundError:
    print("XML ファイルが見つかりませんでした。新規作成します。") 
    root = ET.Element("rss", version="2.0")
    channel = ET.SubElement(root, "channel")
    ET.SubElement(channel, "title").text = "乃木坂 TikTok Videos"
    ET.SubElement(channel, "link").text = "https://www.tiktok.com/"
    ET.SubElement(channel, "description").text = "Latest TikTok videos"

existing_titles = set()
for item in channel.findall('item'):
    title = item.find('title').text
    existing_titles.add(title)
print(f"既存タイトル: {existing_titles}") 

discord_notify = []

print("----- TikTok ページアクセス開始 -----") 
driver.get("https://www.tiktok.com/@nogizaka46_official?lang=jp")

print("----- 待機条件1: body 要素の出現 -----") 
wait = WebDriverWait(driver, 120)

# 複数の待機条件をすべて満たすまで待つ
wait.until(
    lambda driver: (
        EC.presence_of_element_located((By.TAG_NAME, 'body'))(driver) and
        EC.presence_of_element_located((By.CLASS_NAME, 'css-hz5yk3-DivVideoFeedV2 ecyq5ls0'))(driver) and
        EC.presence_of_element_located((By.CLASS_NAME, 'css-x6y88p-DivItemContainerV2'))(driver)
    )
)

print("body 要素、動画フィード、動画コンテナが見つかりました。") 

# スクロール前に動画コンテナを取得
target_container = driver.find_element(By.CLASS_NAME, 'css-x6y88p-DivItemContainerV2')

print("----- スクロール開始 -----") 
# 3回スクロールして出てくる動画を取得
for i in range(3):
    driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.END)
    print(f"{i+1}回目のスクロール完了") 
    time.sleep(5)  # スクロール間隔を延長

print("----- 動画コンテナ取得 -----") 
print(f"動画コンテナ: {target_container}")  # 取得したコンテナを出力

# ここから先は target_container を使って動画情報を取得する処理
# ... 

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
    print(f"XML ファイル '{xml_file}' を保存しました。") 

driver.quit()
print("----- 処理完了 -----")
