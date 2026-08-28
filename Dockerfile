FROM python:3.10-slim

# Instala a biblioteca do SQLite3 necessária pelo Hydrogram
RUN apt-get update && apt-get install -y sqlite3 libsqlite3-dev && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copia as dependências e instala
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia todo o projeto (server.py, .session, etc)
COPY . .

EXPOSE 8080

CMD ["python", "server.py"]
