# Каталог для приложения

Папка `catalog-tools` содержит скрипты сбора каталога. Файл `.github/workflows/update-catalog.yml`
запускает их раз в неделю на GitHub и сохраняет свежий `catalog-tools/catalog.csv`.
Приложение скачивает этот файл по ссылке вида
`https://raw.githubusercontent.com/ВАШ_ЛОГИН/ИМЯ_РЕПОЗИТОРИЯ/main/catalog-tools/catalog.csv`
