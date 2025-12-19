import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import random
import csv

def scrape_batdongsan_links(base_categories, num_pages=2, output_file="links_batdongsan.csv"):
    """
    Hàm cào danh sách link bất động sản.
    :param base_categories: Danh sách các URL danh mục gốc.
    :param num_pages: Số lượng trang muốn cào cho mỗi danh mục.
    :param output_file: Tên file CSV đầu ra.
    """
    
    # 1. Khởi tạo danh sách URL cần chạy
    urls = []
    for cat in base_categories:
        urls.append(cat) # Trang 1
        for i in range(2, num_pages + 1):
            urls.append(f"{cat}/p{i}")

    all_links = [] 
    count = 0

    # Danh sách từ khóa mở rộng theo yêu cầu
    valid_keywords = [
        "ban-can-ho-chung-cu", "ban-can-ho-chung-cu-mini", "ban-nha-rieng", 
        "ban-nha-biet-thu-lien-ke", "ban-nha-mat-pho", "ban-shophouse-nha-pho-thuong-mai", 
        "ban-dat-nen-du-an", "ban-dat", "ban-trang-trai-khu-nghi-duong", 
        "ban-condotel", "ban-kho-nha-xuong"
    ]

    # 2. Khởi tạo file CSV và ghi tiêu đề
    with open(output_file, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['STT', 'URL'])

    # 3. Vòng lặp chính
    for url in urls:
        print(f"\n--- Đang xử lý: {url} ---")
        
        options = uc.ChromeOptions()
        options.add_argument('--headless=new') 
        options.add_argument('--window-size=1920,1080') 
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

        driver = None
        try:
            driver = uc.Chrome(options=options)
            driver.set_page_load_timeout(40)
            driver.get(url)
            
            print("Đang đợi trang render dữ liệu...")
            wait = WebDriverWait(driver, 15)
            
            try:
                wait.until(EC.presence_of_element_located((By.CLASS_NAME, "re__card-info")))
            except:
                print("Hết thời gian chờ class chính, thử quét dữ liệu hiện có...")

            # Tìm kiếm link
            items = driver.find_elements(By.CSS_SELECTOR, "a.js-listing-product")
            if not items:
                try:
                    container = driver.find_element(By.ID, "product-lists-web")
                    items = container.find_elements(By.TAG_NAME, "a")
                except:
                    driver.save_screenshot(f"debug_{int(time.time())}.png")
                    items = []

            current_page_links = []

            for link in items:
                href = link.get_attribute("href")
                # Kiểm tra link hợp lệ dựa trên danh sách keywords mở rộng
                if href and any(key in href for key in valid_keywords):
                    if href not in all_links:
                        all_links.append(href)
                        current_page_links.append(href)
                        count += 1
            
            # Ghi dữ liệu vào CSV ngay lập tức
            if current_page_links:
                with open(output_file, mode='a', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    for l in current_page_links:
                        # Tính toán STT đúng
                        stt = count - len(current_page_links) + current_page_links.index(l) + 1
                        writer.writerow([stt, l])
                print(f"Thành công! Lấy thêm được {len(current_page_links)} link.")
            else:
                print("Không tìm thấy link mới.")

        except Exception as e:
            print(f"Lỗi tại {url}: {e}")
        
        finally:
            if driver:
                driver.quit()
                print("Đã đóng trình duyệt.")
            
            # Thời gian nghỉ ngẫu nhiên để tránh bị block
            time.sleep(random.uniform(5, 8))

    return all_links

# --- CÁCH SỬ DỤNG HÀM ---
if __name__ == "__main__":
    # Tập trung vào danh mục tổng theo yêu cầu
    danh_muc_muc_tieu = [
        "https://batdongsan.com.vn/nha-dat-ban"
    ]
    
    # Gọi hàm: cào số lượng trang bạn mong muốn
    results = scrape_batdongsan_links(danh_muc_muc_tieu, num_pages=2)
    
    print(f"\n--- HOÀN THÀNH ---")
    print(f"Tổng cộng thu thập được: {len(results)} link.")