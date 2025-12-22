from bs4 import BeautifulSoup
import re
import unidecode
from urllib.parse import urlparse
from datetime import datetime

SALE_PROPERTY_TYPES = {
    "ban-can-ho-chung-cu": "Apartment",
    "ban-can-ho-chung-cu-mini": "Mini Apartment",
    "ban-nha-rieng": "Private House",
    "ban-nha-biet-thu-lien-ke": "Villa/Townhouse",
    "ban-nha-mat-pho": "Storefront House",
    "ban-shophouse-nha-pho-thuong-mai": "Shophouse",
    "ban-dat-nen-du-an": "Project Land",
    "ban-dat": "Land Plot",
    "ban-trang-trai-khu-nghi-duong": "Farm/Resort",
    "ban-condotel": "Condotel",
    "ban-kho-nha-xuong": "Warehouse/Factory"
}

RENT_PROPERTY_TYPES = {
    "cho-thue-can-ho-chung-cu": "Apartment",
    "cho-thue-can-ho-chung-cu-mini": "Mini Apartment",
    "cho-thue-nha-rieng": "Private House",
    "cho-thue-nha-biet-thu-lien-ke": "Villa/Townhouse",
    "cho-thue-nha-mat-pho": "Storefront House",
    "cho-thue-shophouse-nha-pho-thuong-mai": "Shophouse",
    "cho-thue-dat": "Land Plot",
    "cho-thue-trang-trai-khu-nghi-duong": "Farm/Resort",
    "cho-thue-condotel": "Condotel",
    "cho-thue-kho-nha-xuong": "Warehouse/Factory",
    "cho-thue-van-phong": "Office Space",
    "cho-thue-cua-hang-ki-ot": "Shop/Kiosk",
    "cho-thue-phong-tro": "Room"
}

ALL_PROPERTY_TYPES = {**SALE_PROPERTY_TYPES, **RENT_PROPERTY_TYPES}

TRANSACTION_TYPE_PATTERNS = {
    "sale": r'^ban-',
    "rent": r'^cho-thue-'
}

SPEC_KEY_MAPPING = {
    "khoang_gia": "price",
    "dien_tich": "area",
    "so_phong_ngu": "bedroom",
    "so_phong_tam_ve_sinh": "bathroom",
    "so_tang": "num_floor",
    "huong_nha": "orientation",
    "huong_ban_cong": "balcony_direction",
    "mat_tien": "front_width",
    "duong_vao": "road_width",
    "phap_ly": "legal",
    "noi_that": "furniture",
    "thoi_gian_du_kien_vao_o": "exdate",
    "muc_gia_dien": "electricity",
    "muc_gia_nuoc": "water",
    "muc_gia_internet": "internet",
    "tien_ich": "utilities"
}

POST_ID_PATTERN = re.compile(r"pr(\d+)$")


def normalize_key(key):
    key = unidecode.unidecode(key).lower()
    key = re.sub(r'[\s,]+', '_', key)
    key = re.sub(r'[^\w_]', '', key)
    key = re.sub(r'_+', '_', key)
    return key.strip('_')


def clean_dict(data):
    cleaned = {}
    for key, value in data.items():
        if value is None:
            continue
        if isinstance(value, str) and not value.strip():
            continue
        if isinstance(value, dict):
            cleaned_nested = clean_dict(value)
            if cleaned_nested:
                cleaned[key] = cleaned_nested
            continue
        if isinstance(value, list) and not value:
            continue
        cleaned[key] = value
    return cleaned


def get_text(soup, selector, default=None):
    tag = soup.select_one(selector)
    return tag.get_text(strip=True) if tag else default


def get_post_id(url):
    match = POST_ID_PATTERN.search(url)
    return match.group(1) if match else None


def classify_property_type(url):
    path = urlparse(url).path.strip('/').lower()
    sorted_types = sorted(
        ALL_PROPERTY_TYPES.items(),
        key=lambda x: len(x[0]),
        reverse=True
    )
    for path_segment, category in sorted_types:
        if path.startswith(path_segment):
            is_full_match = len(path) == len(path_segment)
            if is_full_match or path[len(path_segment)] in ('-'):
                return category
    return "Unknown"


def classify_transaction_type(url):
    path = urlparse(url).path.strip('/').lower()
    for transaction_type, pattern in TRANSACTION_TYPE_PATTERNS.items():
        if re.match(pattern, path):
            return transaction_type
    return "Unknown"


def get_coordinate(html_content):
    geo = {}
    keys = ['latitude', 'longitude']
    for key in keys:
        pattern = rf'["\']?{re.escape(key)}["\']?\s*:\s*(-?[\d\.]+)'
        match = re.search(pattern, html_content)
        if match:
            geo[key] = float(match.group(1).replace(' ', ''))
    return geo


def get_specs(soup):
    specs = {}
    for item in soup.select(".re__pr-specs-content-item"):
        label_tag = item.select_one(".re__pr-specs-content-item-title")
        value_tag = item.select_one(".re__pr-specs-content-item-value")
        if label_tag and value_tag:
            key = normalize_key(label_tag.get_text(strip=True))
            value = value_tag.get_text(strip=True)
            specs[key] = value
    return specs


def get_sub_info(soup):
    sub_info = {}
    for item in soup.select("div.re__pr-short-info-item"):
        title_tag = item.select_one("span.title")
        value_tag = item.select_one("span.value")
        if title_tag and value_tag:
            key = normalize_key(title_tag.get_text(strip=True))
            value = value_tag.get_text(strip=True)
            sub_info[key] = value
    return sub_info


def get_agent_info(soup):
    agent_info = {}
    contact_box = soup.find("div", class_="re__ldp-contact-box")
    agent_infor = contact_box.find("div", class_="re__agent-infor re__agent-name")
    if agent_infor:
        name_tag = (
                agent_infor.find("a", class_="re__contact-name") or
                agent_infor.find("a", class_="js__agent-contact-name")
        )
        if name_tag:
            agent_info['name'] = name_tag.get_text(strip=True)
            href = name_tag.get('href')
            if href:
                agent_info['profile_url'] = href
    avatar_tag = soup.select_one("img.re__contact-avatar")
    if avatar_tag:
        src = avatar_tag.get('src')
        if src:
            agent_info['avatar_url'] = src
    phone_tag = soup.select_one("div.js__phone")
    if phone_tag:
        phone_span = phone_tag.find('span')
        if phone_span:
            agent_info['phone_invisible'] = phone_span.get_text(strip=True)
    zalo_tag = soup.select_one("a.js__zalo-chat")
    if zalo_tag:
        data_href = zalo_tag.get('data-href')
        if data_href:
            agent_info['zalo_url'] = data_href
    other_agent_info = soup.select("div.re__agent-experiment div.agent-deail-infor")
    for item in other_agent_info:
        label_tag = item.select_one("span")
        value_tag = item.select_one("i")
        if label_tag and value_tag:
            label = label_tag.get_text(strip=True).lower()
            value = value_tag.get_text(strip=True)
            if "tham gia" in label:
                agent_info["join_duration"] = value
            elif "tin đăng" in label:
                agent_info["listings"] = value
    return agent_info


def get_project_info(soup):
    project_info = {}
    card = soup.select_one("div.re__ldp-project-info")
    title = get_text(card, "div.re__project-title")
    if title:
        project_info["name"] = title
    for item in card.select("span.re__prj-card-config-value"):
        text = item.get_text(strip=True)
        aria_label = unidecode.unidecode(item.get("aria-label", "")).lower()
        if "trang thai" in aria_label:
            project_info["status"] = text
        elif "gia" in aria_label:
            project_info["price"] = text
    investor = get_text(card, "span.re__prj-card-config-value i.re__icon-office--sm + span.re__long-text")
    if investor:
        project_info["investor"] = investor
    img = card.select_one("div.re__section-avatar img")
    if img:
        src = img.get("src")
        if src:
            project_info["image"] = src
    link = card.select_one("div.re__section-avatar a")
    if link:
        href = link.get("href")
        if href:
            project_info["project_url"] = href
    a_tag = card.select_one("a.re__link-pr span")
    if a_tag:
        text = a_tag.get_text(strip=True)
        match = re.search(r'\d+', text.replace(',', ''))
        if match:
            project_info["listing_count"] = int(match.group())
    return project_info


def get_description(soup):
    prefix = "Thông tin mô tả"
    description_tag = soup.select_one(".re__pr-description")
    description = description_tag.get_text(strip=True)
    if description.startswith(prefix):
        description = description[len(prefix):].strip()
    return description if description else None


def get_images(soup):
    images = []
    for item in soup.select("div.re__media-thumb-item.js__media-thumbs-item"):
        img_tag = item.find("img")
        if img_tag:
            img_url = img_tag.get("data-src") or img_tag.get("src")
            if img_url:
                images.append(img_url)
    return images


def parse_detail_page(html_content, url):
    post_id = get_post_id(url)
    soup = BeautifulSoup(html_content, "lxml")
    title = get_text(soup, "h1")
    address = get_text(soup, "span.re__pr-short-description")
    price_per_spm = get_text(soup, "span.ext")
    description = get_description(soup)
    images = get_images(soup)
    coords = get_coordinate(html_content)
    agent_info = get_agent_info(soup)
    sub_info = get_sub_info(soup)
    specs = get_specs(soup)

    spec_data = {}
    for key, value in specs.items():
        mapped_key = SPEC_KEY_MAPPING.get(key, key)
        if mapped_key not in ['price', 'area']:
            spec_data[mapped_key] = value

    data = {
        "post_id": post_id,
        "property_url": url,
        "transaction_type": classify_transaction_type(url),
        "property_category": classify_property_type(url),
        "title": title,
        "address": address,
        "latitude": coords.get('latitude'),
        "longitude": coords.get('longitude'),
        "price": specs.get("khoang_gia"),
        "price_per_spm": price_per_spm,
        "area": specs.get("dien_tich"),
        "spec": spec_data,
        "description": description,
        "images": images,
        "date_posted": sub_info.get("ngay_dang"),
        "date_expired": sub_info.get("ngay_het_han"),
        "news_type": sub_info.get("loai_tin"),
        "contact_info": agent_info,
        "scraped_at": datetime.now().isoformat()
    }
    return clean_dict(data)
