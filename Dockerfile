# Imagem oficial do Python
FROM python:3.12-slim

# Evita criação de arquivos .pyc
ENV PYTHONDONTWRITEBYTECODE=1

ENV PYTHONUNBUFFERED=1

# Diretório da aplicação
WORKDIR /app

# Copia somente requirements para aproveitar cache
COPY requirements.txt .

# Instala dependências
RUN pip install --no-cache-dir -r requirements.txt

# Copia todo o projeto
COPY . .

# Porta utilizada pelo FastAPI
EXPOSE 8000

# Inicializa a aplicação
#CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]