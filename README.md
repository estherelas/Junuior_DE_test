# Junuior_DE_test
Проект для сбора и анализа данных  с использованием ClickHouse и Docker.
репозиторий

<img width="1396" height="275" alt="image" src="https://github.com/user-attachments/assets/8d30a4ff-5d34-43f6-a1d1-78aa55ff5ee5" />


Функциональность

    Автоматический опрос API (http://api.open-notify.org/astros.json) каждые 60 секунд

    Сохранение сырых данных в ClickHouse

    Автоматический парсинг JSON данных через материализованное представление (тут есть проблема с подключением к клиенту Clickhouse,
    чтобы автоматическом режиме загружать данные. 1. Создала config и user .xml 
    2. Перезапускала контейнер с разными параметрами 
    3. Заранее убивала все процессы запущенные на указанных портах, но так и не поняла в чем проблема)

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

3. Файл init.sql

  Таблицы и представления

        2.1. raw_table - таблица для хранения сырых данных в формате JSON

                data (String) - сырые JSON-данные

                _inserted_at (DateTime) - метка времени добавления записи

        2.2. parsed_table - таблица для хранения структурированных данных

            craft (String) - название  корабля

            name (String) - имя 

            _inserted_at (DateTime) - метка времени добавления записи

        2.3. parsed_mv - материализованное представление для автоматического преобразования данных из raw_table в parsed_table


3. Файл load_to_clikhouse.py
   
    Название функции	                    Назначение и описание
   
    fetch_data()	                        Получает данные с API Open Notify о людях в космосе. Возвращает JSON-данные или None в случае ошибки.                                               Обрабатывает исключения запросов и логирует ошибки.
   
    insert_data(data)	                    Вставляет сырые JSON-данные в таблицу ClickHouse. Принимает словарь с данными, преобразует в JSON-                                                  строку и добавляет метку времени. Возвращает статус операции (True/False).
    fetch_and_insert_data()	                Координирует процесс получения данных с API и их сохранения в БД. Объединяет функции fetch_data() и                                                 insert_data(), возвращая общий статус выполнения.
   
    create_parsed_table_and_view()	        Создает структуру БД: таблицу для структурированных данных и материализованное представление для                                                    автоматического парсинга JSON из сырых данных.
   
   process_with_retry(max_attempts=5)	    Реализует логику повторных попыток с экспоненциальной задержкой. Выполняет попытки обработки данных                                                 с увеличивающимися интервалами между ними.
   
    main()	                                Основная функция приложения. Инициализирует структуру БД и запускает бесконечный цикл опроса API с                                                  обработкой ошибок и поддержкой graceful shutdown.
