"""Сервис синхронизации с Google Sheets."""

import logging
from datetime import date, datetime, timedelta
from typing import Optional

from bot.config import settings

logger = logging.getLogger(__name__)

# Цвета для ячеек (RGB в формате 0-1)
COLOR_YELLOW = {"red": 1.0, "green": 0.95, "blue": 0.6}  # Отправлено
COLOR_GREEN = {"red": 0.7, "green": 0.9, "blue": 0.7}  # Ответ получен
COLOR_WHITE = {"red": 1.0, "green": 1.0, "blue": 1.0}  # Без цвета


class GoogleSheetsService:
    """Сервис для работы с Google Sheets."""

    def __init__(self):
        self._client = None
        self._spreadsheet = None
        self._worksheet = None
        self._plant_rows: dict[str, int] = {}  # plant_id -> row number
        self._date_cols: dict[str, int] = {}  # date string -> column number

    async def init(self):
        """Инициализация подключения к Google Sheets."""
        if not settings.google_sheets_enabled:
            logger.info("Google Sheets интеграция отключена")
            return

        try:
            import gspread
            from google.oauth2.service_account import Credentials

            scopes = [
                "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive",
            ]

            credentials = Credentials.from_service_account_file(
                settings.google_sheets_credentials_file, scopes=scopes
            )

            self._client = gspread.authorize(credentials)
            self._spreadsheet = self._client.open_by_key(
                settings.google_sheets_spreadsheet_id
            )

            # Используем лист "Календарь" или создаём новый
            try:
                self._worksheet = self._spreadsheet.worksheet("Календарь")
            except gspread.WorksheetNotFound:
                self._worksheet = self._spreadsheet.add_worksheet(
                    title="Календарь", rows=50, cols=100
                )
                # Добавляем заголовок первого столбца
                self._worksheet.update_cell(1, 1, "Растение")

            # Загружаем существующие данные
            await self._load_structure()

            # Создаём колонки на 30 дней вперёд
            await self._ensure_date_columns_for_period(days=30)

            logger.info("Google Sheets подключён успешно")

        except Exception as e:
            logger.error(f"Ошибка подключения к Google Sheets: {e}")
            self._client = None

    async def init_plants(self, plant_names: list[str]):
        """Инициализировать строки для всех растений."""
        if not settings.google_sheets_enabled or not self._worksheet:
            return

        try:
            for name in plant_names:
                await self._ensure_plant_row(name)
            logger.info(f"Инициализировано {len(plant_names)} растений в таблице")
        except Exception as e:
            logger.error(f"Ошибка инициализации растений: {e}")

    async def _load_structure(self):
        """Загрузить структуру таблицы (строки растений и столбцы дат)."""
        if not self._worksheet:
            return

        try:
            # Загружаем первый столбец (названия растений)
            plant_names = self._worksheet.col_values(1)
            for i, name in enumerate(plant_names[1:], start=2):  # Пропускаем заголовок
                if name:
                    # Сохраняем по имени, потом сопоставим с ID
                    self._plant_rows[name] = i

            # Загружаем первую строку (даты)
            dates = self._worksheet.row_values(1)
            for i, date_str in enumerate(dates[1:], start=2):  # Пропускаем "Растение"
                if date_str:
                    self._date_cols[date_str] = i

        except Exception as e:
            logger.error(f"Ошибка загрузки структуры таблицы: {e}")

    def _get_date_str(self, d: date = None) -> str:
        """Получить строку даты в формате DD.MM."""
        if d is None:
            d = date.today()
        return d.strftime("%d.%m")

    async def _ensure_plant_row(self, plant_name: str) -> int:
        """Убедиться, что строка для растения существует."""
        if not self._worksheet:
            return -1

        if plant_name in self._plant_rows:
            return self._plant_rows[plant_name]

        try:
            # Находим следующую пустую строку
            all_values = self._worksheet.col_values(1)
            next_row = len(all_values) + 1

            # Добавляем растение
            self._worksheet.update_cell(next_row, 1, plant_name)
            self._plant_rows[plant_name] = next_row

            logger.debug(f"Добавлена строка для растения: {plant_name} (row {next_row})")
            return next_row

        except Exception as e:
            logger.error(f"Ошибка добавления строки растения: {e}")
            return -1

    async def _ensure_date_column(self, d: date = None) -> int:
        """Убедиться, что столбец для даты существует."""
        if not self._worksheet:
            return -1

        date_str = self._get_date_str(d)

        if date_str in self._date_cols:
            return self._date_cols[date_str]

        try:
            # Находим правильную позицию для вставки (по порядку дат)
            target_date = d if d else date.today()
            insert_col = 2  # После столбца "Растение"

            # Находим позицию, куда вставить дату по порядку
            for existing_date_str, col in sorted(self._date_cols.items(), key=lambda x: x[1]):
                try:
                    existing_day, existing_month = map(int, existing_date_str.split("."))
                    existing_date = date(target_date.year, existing_month, existing_day)
                    if target_date > existing_date:
                        insert_col = col + 1
                except:
                    continue

            # Если столбец уже занят, добавляем в конец
            all_values = self._worksheet.row_values(1)
            if insert_col <= len(all_values):
                insert_col = len(all_values) + 1

            # Добавляем дату
            self._worksheet.update_cell(1, insert_col, date_str)
            self._date_cols[date_str] = insert_col

            logger.debug(f"Добавлен столбец для даты: {date_str} (col {insert_col})")
            return insert_col

        except Exception as e:
            logger.error(f"Ошибка добавления столбца даты: {e}")
            return -1

    async def _ensure_date_columns_for_period(self, days: int = 30):
        """Создать колонки дат на указанный период."""
        if not self._worksheet:
            return

        try:
            today = date.today()
            dates_to_add = []

            # Собираем все даты, которых ещё нет
            for i in range(days):
                d = today + timedelta(days=i)
                date_str = self._get_date_str(d)
                if date_str not in self._date_cols:
                    dates_to_add.append((d, date_str))

            if not dates_to_add:
                return

            # Получаем текущее количество столбцов
            all_values = self._worksheet.row_values(1)
            next_col = len(all_values) + 1

            # Добавляем все даты пакетом
            cells_to_update = []
            for d, date_str in dates_to_add:
                self._date_cols[date_str] = next_col
                cells_to_update.append((1, next_col, date_str))
                next_col += 1

            # Обновляем пакетом для скорости
            for row, col, value in cells_to_update:
                self._worksheet.update_cell(row, col, value)

            logger.info(f"Добавлено {len(dates_to_add)} столбцов дат")

        except Exception as e:
            logger.error(f"Ошибка создания столбцов дат: {e}")

    async def _set_cell_color(self, row: int, col: int, color: dict):
        """Установить цвет ячейки."""
        if not self._worksheet:
            return

        try:
            self._worksheet.format(
                f"{_col_letter(col)}{row}",
                {"backgroundColor": color}
            )
        except Exception as e:
            logger.error(f"Ошибка установки цвета ячейки: {e}")

    async def mark_scheduled(self, plant_name: str, scheduled_date: date = None):
        """Отметить запланированное действие (без цвета, только метка)."""
        if not settings.google_sheets_enabled or not self._worksheet:
            return

        try:
            row = await self._ensure_plant_row(plant_name)
            col = await self._ensure_date_column(scheduled_date)

            if row > 0 and col > 0:
                # Ставим метку "📋" если ячейка пустая
                current = self._worksheet.cell(row, col).value
                if not current:
                    self._worksheet.update_cell(row, col, "📋")
                    logger.debug(f"Запланировано: {plant_name} на {self._get_date_str(scheduled_date)}")

        except Exception as e:
            logger.error(f"Ошибка отметки запланированного: {e}")

    async def mark_sent(self, plant_name: str, sent_date: date = None):
        """Отметить отправленное уведомление (жёлтый цвет)."""
        if not settings.google_sheets_enabled or not self._worksheet:
            return

        try:
            row = await self._ensure_plant_row(plant_name)
            col = await self._ensure_date_column(sent_date)

            if row > 0 and col > 0:
                # Обновляем содержимое и цвет
                self._worksheet.update_cell(row, col, "📨")
                await self._set_cell_color(row, col, COLOR_YELLOW)
                logger.debug(f"Отправлено: {plant_name} ({self._get_date_str(sent_date)})")

        except Exception as e:
            logger.error(f"Ошибка отметки отправленного: {e}")

    async def mark_answered(self, plant_name: str, answer: str, answered_date: date = None):
        """Отметить полученный ответ (зелёный цвет)."""
        if not settings.google_sheets_enabled or not self._worksheet:
            return

        try:
            row = await self._ensure_plant_row(plant_name)
            col = await self._ensure_date_column(answered_date)

            if row > 0 and col > 0:
                # Обновляем содержимое и цвет
                self._worksheet.update_cell(row, col, answer)
                await self._set_cell_color(row, col, COLOR_GREEN)
                logger.debug(f"Ответ получен: {plant_name} = {answer} ({self._get_date_str(answered_date)})")

        except Exception as e:
            logger.error(f"Ошибка отметки ответа: {e}")

    async def sync_scheduled_dates(self, plants_schedule: dict[str, list[date]]):
        """
        Синхронизировать запланированные даты для всех растений.
        
        Args:
            plants_schedule: {plant_name: [date1, date2, ...]}
        """
        if not settings.google_sheets_enabled or not self._worksheet:
            return

        for plant_name, dates in plants_schedule.items():
            for d in dates:
                await self.mark_scheduled(plant_name, d)


def _col_letter(col_num: int) -> str:
    """Преобразовать номер столбца в букву (1 -> A, 27 -> AA)."""
    result = ""
    while col_num > 0:
        col_num, remainder = divmod(col_num - 1, 26)
        result = chr(65 + remainder) + result
    return result


# Глобальный экземпляр
sheets_service = GoogleSheetsService()
