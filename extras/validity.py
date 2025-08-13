import requests
import time


def is_existing_amazon_url(url: str) -> bool:
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(url, headers=headers, timeout=10)
        print(r.status_code, r.text)
        return r.status_code == 200 and "Amazon" in r.text
    except requests.RequestException as e:
        print(f"Error: {e}")
        return False


def is_existing_keyword(keyword: str) -> bool:
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(keyword_url, headers=headers, timeout=10)
        print(r.status_code, r.text)
        return r.status_code == 200 and "Amazon" in r.text
    except requests.RequestException as e:
        print(f"Error: {e}")
        return False

# Example
product_url = "https://www.amazon.com/dp/B0C9H2F7PV"
category_url = "https://www.amazon.com/s?k=laptop&crid=20906681248&sprefix=laptop%2Caps%2C208&ref=nb_sb_noss_2"
keyword = "laptop"
keyword_url = f"https://www.amazon.com/s?k={keyword}"

print(is_existing_amazon_url(product_url))
time.sleep(3)
print(is_existing_amazon_url(category_url))
time.sleep(3)
print(is_existing_keyword(keyword))





