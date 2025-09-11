# Usamos una imagen oficial y ligera de Python
FROM python:3.11-slim

# Creamos una carpeta para nuestra aplicación
WORKDIR /app

# Copiamos primero la lista de herramientas
COPY requirements.txt ./

# Instalamos las herramientas
RUN pip install --no-cache-dir -r requirements.txt

# Copiamos el resto de nuestro código
COPY . .

# El comando para arrancar nuestro programa
CMD ["python", "main.py"]
