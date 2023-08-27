from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

from selenium import webdriver

print("Selenium version:", webdriver.__version__)
if 'webdriver' in globals():
    print("webdriver is imported successfully!")
else:
    print("webdriver is not imported.")

options = webdriver.ChromeOptions()
options.add_argument("--headless")  # ヘッドレスモード

driver = webdriver.Chrome(options=options)

driver.get("https://www.tiktok.com/@nogizaka46_official?lang=jp")

wait = WebDriverWait(driver, 10)
wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, "tiktok-x6y88p-DivItemContainerV2")))

for _ in range(3):
    driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.END)
    time.sleep(2)

div_containers = driver.find_elements_by_class_name("tiktok-x6y88p-DivItemContainerV2")

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
