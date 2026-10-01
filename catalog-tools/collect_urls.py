"""Шаг 1: собираем адреса всех товаров из карты сайта optorg.ru.

Запуск:  python collect_urls.py
Результат: файл product_urls.csv (адрес, номер товара, категория)
"""
import csv
import re
import time

import requests

INDEX_URL = "https://optorg.ru/sitemap.xml"
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; StockCheckBot/0.1)"}
PAUSE = 1.5  # секунд между запросами, чтобы не нагружать сайт

# Адрес товара выглядит так: /catalog/<категории>/<номер>/
PRODUCT_RE = re.compile(r"^https://optorg\.ru/catalog/(.+)/(\d+)/$")


def get_locs(url: str) -> list:
    """Скачивает XML-файл карты и возвращает все адреса из тегов <loc>."""
    response = requests.get(url, headers=HEADERS, timeout=30)
    response.raise_for_status()
    return re.findall(r"<loc>\s*(.*?)\s*</loc>", response.text)


def classify(locs: list) -> tuple:
    """Делит адреса на вложенные карты и товары."""
    sitemaps, products = [], []
    for loc in locs:
        if loc.endswith(".xml"):
            sitemaps.append(loc)
        else:
            match = PRODUCT_RE.match(loc)
            if match:
                products.append((loc, match.group(2), match.group(1)))
    return sitemaps, products


def main():
    queue = [INDEX_URL]
    seen = set()
    all_products = {}
    while queue:
        url = queue.pop(0)
        if url in seen:
            continue
        seen.add(url)
        try:
            locs = get_locs(url)
        except Exception as error:
            print("Не удалось открыть", url, "->", error)
            continue
        sitemaps, products = classify(locs)
        queue.extend(sitemaps)
        for loc, product_id, category in products:
            all_products[loc] = (loc, product_id, category)
        print(f"{url}: адресов {len(locs)}, товаров {len(products)}")
        time.sleep(PAUSE)

    with open("product_urls.csv", "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["url", "id", "category"])
        writer.writerows(all_products.values())

    print("\nВсего товаров:", len(all_products))
    for row in list(all_products.values())[:5]:
        print(row[0])


if __name__ == "__main__":
    main()
