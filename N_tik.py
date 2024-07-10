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

print("----- XML 読み込み開始 -----") # XML 読み込み開始
try:
    tree = ET.parse(xml_file)
    root = tree.getroot()
    channel = root.find('channel')
    print("XML ファイルを読み込みました。") # XML 読み込み成功
except FileNotFoundError:
    print("XML ファイルが見つかりませんでした。新規作成します。") # XML ファイルが見つからない
    root = ET.Element("rss", version="2.0")
    channel = ET.SubElement(root, "channel")
    ET.SubElement(channel, "title").text = "乃木坂 TikTok Videos"
    ET.SubElement(channel, "link").text = "https://www.tiktok.com/"
    ET.SubElement(channel, "description").text = "Latest TikTok videos"

existing_titles = set()
for item in channel.findall('item'):
    title = item.find('title').text
    existing_titles.add(title)
print(f"既存タイトル: {existing_titles}") # 既存タイトル

discord_notify = []

print("----- TikTok ページアクセス開始 -----") # TikTok ページアクセス開始
driver.get("https://www.tiktok.com/@nogizaka46_official?lang=jp")

print("----- 待機条件1: body 要素の出現 -----") # 待機条件1
WebDriverWait(driver, 60).until(EC.presence_of_element_located((By.TAG_NAME, 'body')))
print("body 要素が見つかりました。") # 待機条件1 成功

print("----- 待機条件2: 動画コンテナの出現 -----") # 待機条件2
wait = WebDriverWait(driver, 60)
# 少なくとも1つの動画コンテナ要素が表示されるまで待機
wait.until(EC.presence_of_element_located((By.CLASS_NAME, "css-1qb12g8-DivThreeColumnContainer eegew6e2"))) 
print("動画コンテナが見つかりました。") # 待機条件2 成功

print("----- スクロール開始 -----") # スクロール開始
# 3回スクロールして出てくる動画を取得
for i in range(3):
    driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.END)
    print(f"{i+1}回目のスクロール完了") # スクロール完了
    time.sleep(2)

print("----- 動画コンテナ取得 -----") # 動画コンテナ取得
div_containers = driver.find_elements(By.CLASS_NAME, "css-1qb12g8-DivThreeColumnContainer eegew6e2")
print(f"動画コンテナ数: {len(div_containers)}") # コンテナ数

print("----- 動画情報取得開始 -----") # 動画情報取得開始
for i, div_container in enumerate(reversed(div_containers)):
    try:
        print(f"----- 動画{i+1}の処理開始 -----") # 動画ごとの処理開始
        video_desc = div_container.find_element(By.CLASS_NAME, "tiktok-16ou6xi-DivTagCardDesc").text
        print(f"動画{i+1} タイトル: {video_desc}") # 動画タイトル

        video_date = current_time
        print(f"動画{i+1} 日付: {video_date}") # 動画日付

        video_url = div_container.find_element(By.CLASS_NAME, "tiktok-1wrhn5c-AMetaCaptionLine").get_attribute('href')
        print(f"動画{i+1} URL: {video_url}") # 動画URL

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
            print(f"動画{i+1} 新規動画として追加しました。") # 新規動画追加
        else:
            print(f"動画{i+1} 既存動画のためスキップします。") # 既存動画スキップ
        
    except Exception as e:
        print(f"動画{i+1}でエラー: {e}") # エラー発生

print("----- Discord 通知開始 -----") # Discord 通知開始
print(f"Discord 通知リスト: {discord_notify}") 

for video in discord_notify:
    data = {
        "content": f"新しい動画があるよ！\n日付: {video['date']}\nタイトル: {video['title']}\nURL: {video['url']}\n"
    }
    requests.post(webhook_url, data=data)
    print(f"動画 '{video['title']}' の通知を送信しました。") # 通知送信完了

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
    print(f"XML ファイル '{xml_file}' を保存しました。") # XML 保存完了

driver.quit()
print("----- 処理完了 -----") # 処理完了
