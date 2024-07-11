import asyncio
from playwright.async_api import async_playwright
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

async def run(playwright):
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

    browser = await playwright.chromium.launch()
    page = await browser.new_page()
    print("----- TikTok ページアクセス開始 -----")
    await page.goto("https://www.tiktok.com/@nogizaka46_official?lang=jp")

    print("----- 動画コンテナの出現を待つ -----")
    await page.wait_for_selector('.css-x6y88p-DivItemContainerV2') 

    print("----- スクロール開始 -----")
    # スクロール処理を3回繰り返す
    for i in range(3):
        await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
        print(f"{i+1}回目のスクロール完了")
        await asyncio.sleep(5)  # スクロール間隔を5秒に設定

    print("----- 動画情報取得開始 -----")
    video_containers = await page.query_selector_all('.css-x6y88p-DivItemContainerV2')
    for i, video_container in enumerate(reversed(video_containers)):
        try:
            print(f"----- 動画{i+1}の処理開始 -----")
            # タイトルを取得
            video_desc_element = await video_container.query_selector('.css-j7du6l-DivTagCardDesc .css-1wrhn5c-AMetaCaptionLine .css-or44y0-DivContainer')
            video_desc = await video_desc_element.inner_text() if video_desc_element else ''
            print(f"動画{i+1} タイトル: {video_desc}")

            # URLを取得
            video_url_element = await video_container.query_selector('.css-j7du6l-DivTagCardDesc .css-1wrhn5c-AMetaCaptionLine')
            video_url = await video_url_element.get_attribute('href') if video_url_element else ''
            print(f"動画{i+1} URL: {video_url}")

            if video_desc not in existing_titles:
                discord_notify.append({
                    'title': video_desc,
                    'url': video_url,
                    'date': current_time,
                })

                item_elem = ET.SubElement(channel, "item")
                ET.SubElement(item_elem, "title").text = video_desc
                ET.SubElement(item_elem, "url").text = video_url
                ET.SubElement(item_elem, "date").text = current_time
                print(f"動画{i+1} 新規動画として追加しました。")
            else:
                print(f"動画{i+1} 既存動画のためスキップします。")

        except Exception as e:
            print(f"動画{i+1}でエラー: {e}")

    print("----- Discord 通知開始 -----")
    print(f"Discord 通知リスト: {discord_notify}")

    for video in discord_notify:
        data = {
            "content": f"新しい動画があるよ！\n日付: {video['date']}\nタイトル: {video['title']}\nURL: {video['url']}\n"
        }
        requests.post(webhook_url, data=data)
        print(f"動画 '{video['title']}' の通知を送信しました。")

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

    await browser.close()
    print("----- 処理完了 -----")

async def main():
    async with async_playwright() as playwright:
        await run(playwright)

asyncio.run(main())
