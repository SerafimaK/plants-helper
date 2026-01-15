#!/bin/bash
set -e

# Копируем plants.json из образа в volume (перезаписываем при каждом деплое)
if [ -f /app/data.default/plants.json ]; then
    cp /app/data.default/plants.json /app/data/plants.json
    echo "plants.json скопирован в volume"
fi

# Копируем изображения
if [ -d /app/images.default ] && [ "$(ls -A /app/images.default)" ]; then
    cp -r /app/images.default/* /app/images/ 2>/dev/null || true
    echo "Изображения скопированы в volume"
fi

# Запускаем бота
exec python -m bot.main
