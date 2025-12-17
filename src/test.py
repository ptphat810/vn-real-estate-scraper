from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import json
from parser import parse_detail_page
from data_cleaner import clean_all_data


def setup_driver(
        geckodriver_path="geckodriver.exe",
        firefox_binary="C:/Program Files/Mozilla Firefox/firefox.exe",
        headless=False
):
    service = Service(executable_path=geckodriver_path)
    options = Options()
    options.binary_location = firefox_binary
    options.headless = headless
    driver = webdriver.Firefox(service=service, options=options)
    return driver


def scroll_to_bottom(driver, pause_time=2):
    last_height = driver.execute_script("return document.body.scrollHeight")
    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(pause_time)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

def get_rendered_html(url, wait_tag="h1", timeout=15):
    driver = setup_driver()
    driver.get(url)

    try:
        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.TAG_NAME, wait_tag))
        )
        scroll_to_bottom(driver)
        time.sleep(2)  # đợi AJAX load xong
        html = driver.page_source
    finally:
        driver.quit()

    return html


if __name__ == "__main__":
    urls = ["https://batdongsan.com.vn/ban-nha-mat-pho-duong-tran-thanh-mai-phuong-tan-tao/ban-9-ty-204-m2-binh-hcm-pr44814688", "https://batdongsan.com.vn/ban-can-ho-chung-cu-duong-xa-lo-ha-noi-phuong-thao-dien-prj-masteri-thao-dien/ban-2pn-thap-t5-du-an-tro-vay-80-lh-mr-ai-pr44175404"
            , "https://batdongsan.com.vn/ban-dat-duong-vo-van-thu-xa-hung-long-5/sieu-vip-binh-chanh-2-5tr-m2-pr44810318"]
    arr = []
    for url in urls:
        html = get_rendered_html(url)
        raw_data = parse_detail_page(html, url)
        # final_data = clean_all_data(raw_data)
        arr.append(raw_data)

    with open("batdongsan_detail.json", "a", encoding="utf-8") as f:
        for data in arr:
            json.dump(data, f, ensure_ascii=False, indent=4)

    print("Đã xuất dữ liệu sang batdongsan_detail.json")
