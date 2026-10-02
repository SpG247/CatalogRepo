"""Шаг 2: собираем каталог (название + цена) для выбранных разделов.

Нужны файлы в одной папке: check_product.py, product_urls.csv (из collect_urls.py).

КАК ПОЛЬЗОВАТЬСЯ (без командной строки, удобно для Pydroid):
  1. Запустите файл как есть: PREFIX пустой, и скрипт покажет,
     сколько товаров в каждом разделе.
  2. Впишите нужные разделы в PREFIX (несколько через запятую), например:
         PREFIX = "krepej_i_takelaj,avtomobilnye_tovary_shiny"
     Для пробы поставьте LIMIT = 20, потом можно убрать ограничение (LIMIT = None).
  3. Запустите снова. Скрипт можно прерывать и запускать заново:
     уже собранные товары он пропускает, новые добавляет.

При каждом запуске скрипт также наводит порядок в каталоге: убирает товары,
которых больше нет на сайте, и обновляет адреса переехавших товаров.
"""
import csv
import os
import time
from collections import Counter

from check_product import fetch_product

PREFIX = ""      # разделы через запятую, например "krepej_i_takelaj,avtomobilnye_tovary_shiny"
LIMIT = 20       # сколько товаров собрать за запуск (None = без ограничения)
PAUSE = 1.5      # секунд между запросами, чтобы не нагружать сайт

# Для автозапуска на GitHub: настройки можно передать через переменные окружения.
PREFIX = os.environ.get("CATALOG_PREFIX", PREFIX)
LIMIT = int(os.environ.get("CATALOG_LIMIT", LIMIT or 0)) or None
MAX_SECONDS = int(os.environ.get("MAX_SECONDS", "0")) or None  # остановиться через N секунд
PRUNE = os.environ.get("CATALOG_PRUNE", "1") != "0"            # "0" выключает уборку каталога
MAX_REMOVE_SHARE = 0.2  # если пропало больше 20% товаров, уборку не делаем (защита от сбоя)

URLS_FILE = "product_urls.csv"
CATALOG_FILE = "catalog.csv"
FIELDS = ["id", "title", "price", "category", "url"]


def prefixes() -> list:
    return [p.strip().strip("/") for p in PREFIX.split(",") if p.strip()]


def read_urls() -> list:
    with open(URLS_FILE, encoding="utf-8") as file:
        return list(csv.DictReader(file))


def read_catalog() -> list:
    if not os.path.exists(CATALOG_FILE):
        return []
    with open(CATALOG_FILE, encoding="utf-8") as file:
        return list(csv.DictReader(file))


def write_catalog(rows: list) -> None:
    temp = CATALOG_FILE + ".tmp"
    with open(temp, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=FIELDS)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in FIELDS})
    os.replace(temp, CATALOG_FILE)


def show_stats(rows: list) -> None:
    """Печатает, сколько товаров в каждом разделе (два уровня вложенности)."""
    counter = Counter("/".join(row["category"].split("/")[:2]) for row in rows)
    print("Товаров по разделам (раздел/подраздел):\n")
    for name, count in counter.most_common():
        print(f"{count:6}  {name}")
    print("\nСкопируйте нужные разделы в PREFIX (через запятую) и запустите снова.")


def tidy_catalog(url_rows: list) -> None:
    """Убирает из каталога товары, которых нет на сайте, обновляет адреса, удаляет дубли."""
    catalog = read_catalog()
    if not catalog:
        return
    site = {row["id"]: row for row in url_rows}
    if not site:
        print("Карта сайта пуста, уборку каталога пропускаем.")
        return

    seen, kept, removed, moved = set(), [], 0, 0
    for row in catalog:
        product_id = row.get("id")
        if not product_id or product_id in seen:
            continue  # дубль или битая строка
        seen.add(product_id)
        current = site.get(product_id)
        if current is None:
            removed += 1
            continue
        if row.get("url") != current["url"]:
            row["url"], row["category"] = current["url"], current["category"]
            moved += 1
        kept.append(row)

    if len(seen) >= 50 and removed > len(seen) * MAX_REMOVE_SHARE:
        print(f"Из каталога пропало бы {removed} из {len(seen)} товаров, это слишком много. "
              "Похоже на сбой карты сайта, уборку пропускаем.")
        return

    duplicates = len(catalog) - len(seen)
    if removed or moved or duplicates:
        write_catalog(kept)
        print(f"Уборка каталога: удалено {removed} (нет на сайте), "
              f"обновлено адресов {moved}, убрано дублей {duplicates}.")


def crawl(rows: list) -> None:
    done = {row["id"] for row in read_catalog()}

    # Товары выбранных разделов: сначала первый раздел, потом второй и т.д.
    ordered, taken = [], set()
    for prefix in prefixes():
        for row in rows:
            if row["id"] not in taken and row["category"].startswith(prefix):
                ordered.append(row)
                taken.add(row["id"])
    already = sum(1 for row in ordered if row["id"] in done)
    todo = [row for row in ordered if row["id"] not in done]
    print(f"В разделе товаров: {len(ordered)}, уже собрано: {already}")
    if LIMIT:
        todo = todo[:LIMIT]

    started = time.time()
    is_new = not os.path.exists(CATALOG_FILE)
    with open(CATALOG_FILE, "a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        if is_new:
            writer.writerow(FIELDS)
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
    if prefixes():
        if PRUNE:
            tidy_catalog(all_rows)
        crawl(all_rows)
    else:
        show_stats(all_rows)
