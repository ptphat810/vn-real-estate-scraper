from bs4 import BeautifulSoup
import re
import unidecode

def classify_property(url):
    mapping = {
        "ban-can-ho-chung-cu": "Apartment",
        "ban-can-ho-chung-cu-mini": "Apartment",
        "ban-nha-rieng": "House",
        "ban-nha-biet-thu-lien-ke": "House",
        "ban-nha-mat-pho": "House",
        "ban-shophouse-nha-pho-thuong-mai": "House",
        "ban-dat-nen-du-an": "Land",
        "ban-dat": "Land",
        "ban-trang-trai-khu-nghi-duong": "Resort/Investment",
        "ban-condotel": "Resort/Investment",
        "ban-kho-nha-xuong": "Warehouse/Factory"
    }

    for detailed_type, main_group in mapping.items():
        if detailed_type in url:
            return main_group
    return "Unknown"

def normalize_key(key):
    """
    Lowercase, remove accents, replace spaces with underscores
    """
    key = unidecode.unidecode(key)
    key = key.lower().replace(" ", "_")
    return key

def extract_post_id(url):
    """
    Extract the post ID from the URL
    """
    match = re.search(r"pr(\d+)$", url)
    return match.group(1) if match else "NaN"

def parse_detail_page(html_content, url):
    soup = BeautifulSoup(html_content, "lxml")
    """
    Extract information
    """
    # Type of property
    type_property = classify_property(url)

    # Post ID
    post_id = extract_post_id(url)

    # Title
    title = soup.find("h1")
    title = title.get_text(strip=True) if title else "NaN"

    # Address
    address = soup.select_one("span.re__pr-short-description")
    address = address.get_text(strip=True) if address else "NaN"

    # Price per sqm
    price_per_spm = soup.select_one("span.ext")
    price_per_spm = price_per_spm.get_text(strip=True) if price_per_spm else "NaN"

    # Description
    description = soup.select_one(".re__pr-description")
    description = (
        description.get_text(strip=True).replace("Thông tin mô tả", "", 1)
        if description
        else "N/A"
    )

    # IMAGES
    images = []
    for item in soup.select("div.re__media-thumb-item.js__media-thumbs-item"):
        img_tag = item.find("img")
        if img_tag:
            img_url = img_tag.get("data-src") or img_tag.get("src")
            images.append(img_url)

    # OTHER FEATURES
    specs = {}
    items = soup.select(".re__pr-specs-content-item")
    for item in items:
        label_tag = item.select_one(".re__pr-specs-content-item-title")
        value_tag = item.select_one(".re__pr-specs-content-item-value")
        if label_tag and value_tag:
            key = normalize_key(label_tag.get_text(strip=True))
            value = value_tag.get_text(strip=True)
            specs[key] = value

    price = specs.get("khoang_gia", "NaN")
    area = specs.get("dien_tich", "NaN")
    bedroom = specs.get("so_phong_ngu", "NaN")
    bathroom = specs.get("so_phong_tam,_ve_sinh", "NaN")
    num_floor = specs.get("so_tang", "NaN")
    orientation = specs.get("huong_nha", "NaN")
    balcony_direction = specs.get("huong_ban_cong", "NaN")
    front_width = specs.get("mat_tien", "NaN")
    road_width = specs.get("duong_vao", "NaN")
    legal = specs.get("phap_ly", "NaN")
    furniture = specs.get("noi_that", "NaN")

    # Sub-info
    sub_info = {}
    items_02 = soup.select("div.re__pr-short-info-item")
    for item in items_02:
        title_tag = item.select_one("span.title")
        value_tag = item.select_one("span.value")
        if title_tag and value_tag:
            key = normalize_key(title_tag.get_text(strip=True))
            value = value_tag.get_text(strip=True)
            sub_info[key] = value

    date_posted = sub_info.get("ngay_dang", "NaN")
    expire_posted = sub_info.get("ngay_het_han", "NaN")
    type_news = sub_info.get("loai_tin", "NaN")

    data = {
        "post_id": post_id,
        "type_property": type_property,
        "title": title,
        "address": address,
        "price": price,
        "price_per_spm": price_per_spm,
        "spec": {
            "area": area,
            "bedroom": bedroom,
            "bathroom": bathroom,
            "num_floor": num_floor,
            "orientation": orientation,
            "balcony_direction": balcony_direction,
            "front": front_width,
            "road": road_width,
            "legal": legal,
            "furniture": furniture
        },
        "description": description,
        "images": images,
        "property_url": url,
        "date_posted": date_posted,
        "expire_posted": expire_posted,
        "type_news": type_news
    }

    # Remove columns with NaN
    data = {k: v for k, v in data.items() if v not in ("NaN", "N/A")}

    return data


if __name__ == "__main__":
    pass
