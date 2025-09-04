# Junuior_DE_test
Проект для сбора и анализа данных  с использованием ClickHouse и Docker.
репозиторий/
├── Dockerfile                 # Основной файл для сборки образа
├── README.md                 # Этот файл
├── init.sql                  # SQL-скрипт для создания схемы БД (таблицы, представления)
├── load_to_clickhouse.py     # Python-скрипт для загрузки данных
├── config.xml                # Кастомная конфигурация сервера
└── users.xml                 # Кастомные настройки пользователей

Функциональность

    Автоматический опрос API (http://api.open-notify.org/astros.json) каждые 60 секунд

    Сохранение сырых данных в ClickHouse

    Автоматический парсинг JSON данных через материализованное представление (тут есть проблема с подключением к клиенту Clickhouse, чтобы               автоматическом режиме загружать данные. 1. Создала config и user .xml 2. Перезапускала контейнер с разными параметрами 3. Заранее убивала все        процессы запущенные на указанных портах, но так и не поняла в чем проблема)

    Экспоненциальная повторная попытка при ошибках (с максимальным количеством попыток 5)

    Логирование всех операций

Требования

    Python 3.7+

    ClickHouse Server

    Библиотеки Python: clickhouse-driver, requests

 Структура и описание файлов

 1. Dockerfile
    1.1. Сборка образа docker build -t clickhouse-python .
    1.2. Запуск контейнера docker run -it -p 9001:9000 clickhouse-python
    1.3. Описание файла

    1.3.1. Базовый образ
            FROM clickhouse:25.7
    1.3.2. Установка зависимостей
          RUN apt-get update && \
              apt-get install -y python3 python3-pip curl && \
              apt-get clean && \
              pip3 install clickhouse-connect && \
              pip3 install requests && \
              pip install clickhouse-driver && \
              rm -rf /var/lib/apt/lists/*

    Обновляет пакетный менеджер apt и устанавливает Python 3, pip и curl.

    Устанавливает две популярные Python-библиотеки для работы с ClickHouse:clickhouse-connect и clickhouse-driver.

    Также устанавливается библиотека requests для выполнения HTTP-запросов  для получения данных из API.

    Команды очистки (apt-get clean, rm -rf...) уменьшают размер конечного образа.

    1.3.3. Копирование скриптов инициализации

          COPY init.sql /docker-entrypoint-initdb.d/
          COPY load_to_clickhouse.py /docker-entrypoint-initdb.d/

          Копирует файлы init.sql и load_to_clickhouse.py в специальную директорию /docker-entrypoint-initdb.d/. Важная особенность официального               образа ClickHouse: все скрипты (с расширениями .sh и .sql) в этой директории выполняются автоматически при первом запуске контейнера.
    
    1.3.4. Установка прав на выполнение

          RUN chmod +x /docker-entrypoint-initdb.d/*.py

            Делает Python-скрипт исполняемым, что необходимо для его автоматического запуска.
    1.3.5. Копирование конфигурационных файлов

          COPY config.xml /etc/clickhouse-server/config.d/
          COPY users.xml /etc/clickhouse-server/users.d/

          Файлы конфигурации ClickHouse можно кастомизировать, помещая их в директории config.d/ и users.d/ внутри контейнера.

    1.3.6. Открытие портов

            EXPOSE 8123 9000 9009

            Инструкция для Docker, которая сообщает, какие порты контейнер будет слушать. Это метаданные для документации. Фактическое пробрасывание             портов делается командой docker run -p.

    1.3.7. Запуск скрипта 

            CMD ["python3", "/docker-entrypoint-initdb.d/load_to_clickhouse.py"]
