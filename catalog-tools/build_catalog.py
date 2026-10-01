"""Шаг 2: собираем каталог (название + цена) для одного раздела.

Нужны файлы в одной папке: check_product.py, product_urls.csv (из collect_urls.py).

КАК ПОЛЬЗОВАТЬСЯ (без командной строки, удобно для Pydroid):
  1. Запустите файл как есть: PREFIX пустой, и скрипт покажет,
     сколько товаров в каждом разделе.
  2. Выберите раздел, впишите его в PREFIX ниже, например:
         PREFIX = "krepej_i_takelaj/samorezy_shurupy"
     Для пробы поставьте LIMIT = 20, потом можно убрать ограничение (LIMIT = None).
  3. Запустите снова. Скрипт можно прерывать и запускать заново:
     уже собранные товары он пропускает.
"""
import csv
import os
import time
from collections import Counter

from check_product import fetch_product

PREFIX = ""      # раздел для сбора, например "krepej_i_takelaj/samorezy_shurupy"
LIMIT = 20       # сколько товаров собрать за запуск (None = без ограничения)
PAUSE = 1.5      # секунд между запросами, чтобы не нагружать сайт

# Для автозапуска на GitHub: настройки можно передать через переменные окружения.
PREFIX = os.environ.get("CATALOG_PREFIX", PREFIX)
LIMIT = int(os.environ.get("CATALOG_LIMIT", LIMIT or 0)) or None
MAX_SECONDS = int(os.environ.get("MAX_SECONDS", "0")) or None  # остановиться через N секунд

URLS_FILE = "product_urls.csv"
CATALOG_FILE = "catalog.csv"


def read_urls() -> list:
    with open(URLS_FILE, encoding="utf-8") as file:
        return list(csv.DictReader(file))


def show_stats(rows: list) -> None:
    """Печатает, сколько товаров в каждом разделе (два уровня вложенности)."""
    counter = Counter("/".join(row["category"].split("/")[:2]) for row in rows)
    print("Товаров по разделам (раздел/подраздел):\n")
    for name, count in counter.most_common():
        print(f"{count:6}  {name}")
    print("\nСкопируйте нужный раздел в PREFIX и запустите снова.")


def already_done() -> set:
    if not os.path.exists(CATALOG_FILE):
        return set()
    with open(CATALOG_FILE, encoding="utf-8") as file:
        return {row["id"] for row in csv.DictReader(file)}


def crawl(rows: list) -> None:
    todo = [r for r in rows if r["category"].startswith(PREFIX)]
    done = already_done()
    todo = [r for r in todo if r["id"] not in done]
    print(f"В разделе товаров: {len(todo) + len(done)}, уже собрано: {len(done)}")
    if LIMIT:
        todo = todo[:LIMIT]

    started = time.time()
    is_new = not os.path.exists(CATALOG_FILE)
    with open(CATALOG_FILE, "a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        if is_new:
            writer.writerow(["id", "title", "price", "category", "url"])
        for number, row in enumerate(todo, 1):
            if MAX_SECONDS and time.time() - started > MAX_SECONDS:
                print("Достигнут лимит времени, продолжим при следующем запуске.")
                break
            try:
                data = fetch_product(row["url"])
            except Exception as error:
                print(f"{number}/{len(todo)} ошибка {row['id']}: {error}")
                time.sleep(PAUSE)
                continue
            writer.writerow(
                [row["id"], data["title"], data["price"], row["category"], row["url"]]
            )
            file.flush()
            print(f"{number}/{len(todo)}  {data['title']}  {data['price']} руб.")
            time.sleep(PAUSE)
    print("\nГотово. Результат в файле", CATALOG_FILE)


if __name__ == "__main__":
    all_rows = read_urls()
    if PREFIX:
        crawl(all_rows)
    else:
        show_stats(all_rows)
