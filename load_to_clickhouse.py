from clickhouse_driver import Client
import requests
import json
from datetime import datetime
import time
import logging

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# URL API для получения данных о людях в космосе
API_URL = "http://api.open-notify.org/astros.json"

# Конфигурация ClickHouse (лучше вынести в отдельный config файл)
CLICKHOUSE_CONFIG = {
    'host': 'localhost',
    'user': 'default',
    'password': 'password',
    'database': 'db'
}

def fetch_data():
    """Получает данные с API"""
    try:
        response = requests.get(API_URL, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка при запросе к API: {e}")
        return None

def insert_data(data):
    """Вставляет данные в ClickHouse"""
    try:
        client = Client(**CLICKHOUSE_CONFIG)
        json_data = json.dumps(data)
        current_time = datetime.now()
        
        client.execute(
            'INSERT INTO raw_table (data, _inserted_at) VALUES',
            [(json_data, current_time)]
        )
        
        logger.info(f"Данные успешно вставлены в {current_time}")
        return True
    except Exception as e:
        logger.error(f"Ошибка при вставке данных в ClickHouse: {e}")
        return False
    finally:
        if 'client' in locals():
            client.disconnect()

def fetch_and_insert_data():
    """Получает и вставляет данные"""
    data = fetch_data()
    if data:
        return insert_data(data)
    return False

def create_parsed_table_and_view():
    """Создает таблицу и материализованное представление"""
    try:
        client = Client(**CLICKHOUSE_CONFIG)
        
        # Создаем таблицу для парсинга данных
        create_parsed_table_query = """
        CREATE TABLE IF NOT EXISTS db.parsed_table
        (
            craft String,
            name String,
            _inserted_at DateTime
        )
        ENGINE = MergeTree()
        ORDER BY _inserted_at;
        """
        
        client.execute(create_parsed_table_query)
        logger.info("Таблица parsed_table создана успешно")
        
        # Создаем материализованное представление
        create_materialized_view_query = """
        CREATE MATERIALIZED VIEW IF NOT EXISTS db.raw
        TO db.parsed_table 
        AS
        SELECT 
            JSONExtractString(people, 'craft') AS craft,
            JSONExtractString(people, 'name') AS name,
            _inserted_at
        FROM (
            SELECT 
                data,
                _inserted_at,
                JSONExtractArrayRaw(data, 'people') AS people_array
            FROM db.raw_table
        )
        ARRAY JOIN people_array AS people;
        """
        
        client.execute(create_materialized_view_query)
        logger.info("Материализованное представление создано успешно")
        
    except Exception as e:
        logger.error(f"Произошла ошибка: {e}")
    finally:
        if 'client' in locals():
            client.disconnect()

def process_with_retry(max_attempts=5):
    """Обрабатывает данные с нарастающим ретраем и ограничением попыток"""
    base_delay = 5  # Базовая задержка в секундах
    max_delay = 300  # Максимальная задержка в секундах (5 минут)
    
    for attempt in range(1, max_attempts + 1):
        try:
            logger.info(f"Попытка {attempt} из {max_attempts}")
            
            # Получаем и вставляем данные
            success = fetch_and_insert_data()
            
            if success:
                logger.info("Данные успешно обработаны")
                return True
            else:
                logger.warning(f"Ошибка при обработке данных (попытка {attempt})")
            
            # Вычисляем задержку для следующей попытки (экспоненциальный рост)
            delay = min(base_delay * (2 ** (attempt - 1)), max_delay)
            
            if attempt < max_attempts:
                logger.info(f"Следующая попытка через {delay} секунд")
                time.sleep(delay)
                
        except Exception as e:
            logger.error(f"Неожиданная ошибка на попытке {attempt}: {e}")
            if attempt < max_attempts:
                delay = min(base_delay * (2 ** (attempt - 1)), max_delay)
                logger.info(f"Следующая попытка через {delay} секунд")
                time.sleep(delay)
    
    # Если все попытки неудачны
    raise Exception(f"Не удалось обработать данные после {max_attempts} попыток")

def main():
    """Основная функция с нарастающим ретраем и ограничением попыток"""
    logger.info("Запуск процесса опроса API")
    
    # Создаем таблицу и представление
    create_parsed_table_and_view()
    
    while True:
        try:
            # Обрабатываем данные с ретраем
            process_with_retry()
            
            # Успешно обработали, ждем перед следующим запросом
            logger.info("Ожидание 60 секунд перед следующим запросом")
            time.sleep(60)
            
        except Exception as e:
            logger.error(f"Критическая ошибка: {e}")
            logger.info("Ожидание 300 секунд перед следующей попыткой")
            time.sleep(300)
            
        except KeyboardInterrupt:
            logger.info("Получен сигнал прерывания. Завершение работы...")
            break

if __name__ == "__main__":
    main()