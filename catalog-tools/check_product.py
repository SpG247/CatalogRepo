"""Проверка одного товара на optorg.ru: название, цена, наличие по складам.

Установка (один раз):   pip install requests beautifulsoup4
Запуск:                 python check_product.py
или со своей ссылкой:   python check_product.py https://optorg.ru/catalog/.../511913/
"""
import sys

import requests
from bs4 import BeautifulSoup

DEFAULT_URL = (
    "https://optorg.ru/catalog/krepej_i_takelaj/"
    "samorezy_shurupy/samorezy_krovelnye/511913/"
)
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; StockCheckBot/0.1)"}


def parse_product(html: str) -> dict:
    """Достаёт данные из HTML страницы товара."""
    soup = BeautifulSoup(html, "html.parser")

    # Название: берём из заголовка страницы и убираем хвост про магазин
    title = soup.title.get_text(strip=True) if soup.title else ""
    title = title.split(" выгодно купить")[0].strip()

    # Цена: лежит в <meta itemprop="price" content="497">
    price_tag = soup.find("meta", itemprop="price")
    price = price_tag["content"] if price_tag else None

    # Общий признак наличия: InStock / OutOfStock
    avail_tag = soup.find("link", itemprop="availability")
    in_stock = bool(avail_tag and "InStock" in avail_tag.get("href", ""))

    # Наличие по складам (на странице этот блок повторяется, берём первый)
    stores = []
    block = soup.find(class_="quantity_indicator")
    if block:
        for row in block.find_all(class_="store_row"):
            name = row.find(class_="store_row_name")
            value = row.find(class_="store_row_value")
            if name and value:
                stores.append(
                    (name.get_text(" ", strip=True), value.get_text(" ", strip=True))
                )

    return {"title": title, "price": price, "in_stock": in_stock, "stores": stores}


def fetch_product(url: str) -> dict:
    response = requests.get(url, headers=HEADERS, timeout=15)
    response.raise_for_status()
    return parse_product(response.text)


if __name__ == "__main__":
    url = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_URL
    data = fetch_product(url)
    print("Товар:", data["title"])
    print("Цена:", data["price"], "руб." if data["price"] else "не найдена")
    print("В наличии:", "да" if data["in_stock"] else "нет")
    for store, status in data["stores"]:
        print(f"  {store}: {status}")
