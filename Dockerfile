FROM python:3.11-slim

WORKDIR /app

# Установка poetry
RUN pip install poetry

# Копируем файлы зависимостей
COPY pyproject.toml poetry.lock* ./

# Устанавливаем зависимости
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi --only main --no-root

# Копируем код
COPY . .

# Сохраняем дефолтные данные (будут копироваться в volume при старте)
RUN mkdir -p /app/data.default /app/images.default \
    && cp -r /app/data/* /app/data.default/ 2>/dev/null || true \
    && cp -r /app/images/* /app/images.default/ 2>/dev/null || true

# Создаём директории для volume
RUN mkdir -p /app/data /app/images

# Делаем entrypoint исполняемым
RUN chmod +x /app/entrypoint.sh

# Запуск через entrypoint
CMD ["/app/entrypoint.sh"]
