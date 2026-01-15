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

# Создаём директории для данных
RUN mkdir -p data images

# Запуск
CMD ["python", "-m", "bot.main"]
