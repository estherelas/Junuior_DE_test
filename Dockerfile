FROM clickhouse:25.7

RUN apt-get update && \
    apt-get install -y python3 python3-pip curl && \
    apt-get clean && \
    pip3 install clickhouse-connect && \
    pip3 install requests && \
    pip install clickhouse-driver && \
    rm -rf /var/lib/apt/lists/*

# Копирование скриптов инициализации
COPY init.sql /docker-entrypoint-initdb.d/
COPY load_to_clickhouse.py /docker-entrypoint-initdb.d/

# Установка прав на выполнение скриптов
RUN chmod +x /docker-entrypoint-initdb.d/*.py

# Копирование конфигурационных файлов (если нужны кастомные настройки)
COPY config.xml /etc/clickhouse-server/config.d/
COPY users.xml /etc/clickhouse-server/users.d/

# Открытие портов (HTTP, native, interserver)
EXPOSE 8123 9000 9009
CMD ["python3", "/docker-entrypoint-initdb.d/load_to_clickhouse.py"]