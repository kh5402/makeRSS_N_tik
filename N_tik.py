from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

print("Selenium version:", webdriver.__version__)
if 'webdriver' in globals():
    print("webdriver is imported successfully!")
else:
    print("webdriver is not imported.")

options = webdriver.ChromeOptions()
options.add_argument("--headless")  # ヘッドレスモード
options.add_argument('--no-sandbox')
options.add_argument('--disable-setuid-sandbox')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--disable-accelerated-2d-canvas')
options.add_argument('--disable-gpu')
options.binary_location = "/usr/bin/chromium-browser"  # Chromiumのパスを指定

driver = webdriver.Chrome(options=options)

if driver:
    print("WebDriver instance is created successfully!")
else:
    print("Failed to create WebDriver instance.")
print(driver.page_source)

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

for i, div_container in enumerate(div_containers):
    try:
        video_views = div_container.find_element_by_class_name("video-count").text
        video_desc = div_container.find_element_by_class_name("tiktok-16ou6xi-DivTagCardDesc").text
        print(f"動画{i+1}")
        print(f"ビデオの視聴回数: {video_views}")
        print(f"ビデオの説明: {video_desc}")
        print("------")
    except Exception as e:
        print(f"動画{i+1}でエラー: {e}")

driver.quit()
