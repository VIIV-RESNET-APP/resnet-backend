FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt ./

RUN pip install --upgrade pip setuptools
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000
CMD [ "flask", "run","--host","0.0.0.0","--port","5000"]
# Usa una imagen más ligera como base
#FROM python:3.11-slim
#
## Establece el directorio de trabajo en /app
#WORKDIR /app
#
## Copia solo el archivo de requerimientos primero para aprovechar la caché de Docker
#COPY requirements.txt .
#
## Instala las dependencias
#RUN pip install --no-cache-dir -r requirements.txt
#
## Copia el resto de los archivos de la aplicación
#COPY . .
#
## Exponer el puerto en el que la aplicación se ejecutará
#EXPOSE 5000
#
## Usar un servidor WSGI como Gunicorn para producción
#CMD ["gunicorn", "-b", "0.0.0.0:5000", "app:app"]
#
