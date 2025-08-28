FROM python:3.9-slim

WORKDIR /app

# Instalar dependencias del sistema necesarias para las librerías de Python
RUN apt-get update && apt-get install -y \
    netcat-openbsd \
    gcc \
    g++ \
    libpq-dev \
    unixodbc-dev \
    && rm -rf /var/lib/apt/lists/*

# Copiar archivos de dependencias
COPY requirements.txt .

# Instalar dependencias de Python (algunas pueden fallar y no son críticas para MongoDB)
RUN pip install --no-cache-dir flask flask_cors flask_session pymongo bcrypt python-dotenv pandas openpyxl xlsxwriter numpy requests || true
RUN pip install --no-cache-dir psycopg2 || echo "psycopg2 failed - skipping"
RUN pip install --no-cache-dir pyodbc || echo "pyodbc failed - skipping"  
RUN pip install --no-cache-dir msal || echo "msal failed - skipping"
RUN pip install --no-cache-dir oracledb || echo "oracledb failed - skipping"
RUN pip install --no-cache-dir cx_Oracle || echo "cx_Oracle failed - skipping"

# Copiar el código de la aplicación
COPY . .

# Exponer el puerto
EXPOSE 4500

# El comando se define en docker-compose.yml
CMD ["python", "src/main.py"]