import feedparser
import requests
import os
from datetime import datetime, timedelta
import pytz
import xml.etree.ElementTree as ET
from xml.dom import minidom

# Discord webhook URL
webhook_url = os.environ.get('DISCORD_WEBHOOK')

# TikTok RSSフィードのURL (conoro/tiktok-rss-flatを使用)
rss_feed_url = "https://tiktok-rss.vercel.app/nogizaka46_official"

# XMLファイルのパス
xml_file = 'N_tik.xml'  # ファイル名を修正

# タイムゾーンの設定
japan_tz = pytz.timezone('Asia/Tokyo')

def send_discord_notification(video_title, video_link, video_published):
    """Discordに通知を送信する関数"""
    message = f"乃木坂46の新しいTikTok動画！\n\n**{video_title}**\n{video_link}\n\n公開日時: {video_published.astimezone(japan_tz).strftime('%Y-%m-%d %H:%M:%S')}"
    data = {"content": message}
    requests.post(webhook_url, data=data)

def load_existing_videos(xml_file):
    """XMLファイルから既存の動画情報を読み込む"""
    try:
        tree = ET.parse(xml_file)
        root = tree.getroot()
        existing_videos = {item.find('url').text: item.find('date').text for item in root.findall('./channel/item')}
        return existing_videos
    except FileNotFoundError:
        return {}

def save_videos_to_xml(videos, xml_file):
    """動画情報をXMLファイルに保存する"""
    root = ET.Element("rss", version="2.0")
    channel = ET.SubElement(root, "channel")
    ET.SubElement(channel, "title").text = "乃木坂46 TikTok Videos"
    ET.SubElement(channel, "link").text = rss_feed_url
    ET.SubElement(channel, "description").text = "Latest TikTok videos from conoro/tiktok-rss-flat"

    for video_url, video_date in videos.items():
        item_elem = ET.SubElement(channel, "item")
        ET.SubElement(item_elem, "title").text = ""  # タイトルは空欄
        ET.SubElement(item_elem, "url").text = video_url
        ET.SubElement(item_elem, "date").text = video_date

    # XMLファイルを保存 (エンコーディングをUTF-8に設定、改行も入れる)
    tree = ET.ElementTree(root)
    xml_str = ET.tostring(root, encoding='utf-8', method='xml')

    # minidomできれいにフォーマットする
    dom = minidom.parseString(xml_str)
    pretty_xml_str = dom.toprettyxml(indent="  ")

    # 空白行を取り除く
    pretty_xml_str = os.linesep.join([s for s in pretty_xml_str.splitlines() if s.strip()])

    with open(xml_file, 'w', encoding='utf-8') as f:
        f.write(pretty_xml_str)

def main():
    # XMLファイルから既存の動画情報を読み込む
    existing_videos = load_existing_videos(xml_file)

    # RSSフィードを取得
    feed = feedparser.parse(rss_feed_url)

    # 新しい動画があればDiscordに通知し、XMLファイルに保存
    for entry in feed.entries:
        video_url = entry.link
        if video_url in existing_videos:
            continue  # 既存の動画はスキップ

        video_title = entry.title
        video_published = datetime.strptime(entry.published, "%a, %d %b %Y %H:%M:%S %z")

        # 24時間以内に公開された動画のみ通知
        if video_published > datetime.now(pytz.utc) - timedelta(hours=24):
            send_discord_notification(video_title, video_url, video_published)
            existing_videos[video_url] = video_published.astimezone(japan_tz).strftime('%Y-%m-%d %H:%M:%S')

    # 動画情報をXMLファイルに保存
    save_videos_to_xml(existing_videos, xml_file)

if __name__ == "__main__":
    main()
