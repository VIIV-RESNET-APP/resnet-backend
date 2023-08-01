# Resnet Backend

API REST del sistema ResNet

## Tabla de contenidos

- [Descripción](#descripcion)
- [Requisitos previos](#requisitos-previos)
- [Instalación](#instalacion)
- [Uso](#uso)
- [Endpoints](#endpoints)
- [Licencia](#licencia)

## Descripción

Frontend del sistema web ResNet que tiene como propósito extraer y presentar datos de redes de coautoría de investigadores ecuatorianos. Esta herramienta ofrece la posibilidad de visualizar información académica, buscar expertos en áreas de investigación y analizar temas relacionados. Para mejorar la precisión en las búsquedas, se han implementado técnicas de Information Retrieval. El objetivo principal es proporcionar a los usuarios una experiencia eficiente en la exploración y análisis de información académica.

## Requisitos previos

* Python (versión 3.11)
* pip (versión 23.2)

## Instalación

1. Clona el repositorio: `git clone https://github.com/jozuenikolas/resnet-backend.git`
2. Ingresa al directorio del proyecto: `cd resnet-backend`
3. Crea y activa un entorno virtual (opcional pero recomendado): 
```bash
python -m venv venv
source venv/bin/activate   # Para sistemas Unix/Linux
venv\Scripts\activate      # Para sistemas Windows
```
4. Instala las dependencias: pip install -r requirements.txt

## Uso
Para iniciar el servidor, ejecuta el siguiente comando:

```bash
python -m flask run
```

## Endpoints
A continuación se muestran los principales endpoints disponibles en la API:

* GET /authors/get-authors-by-query: Obtiene la lista de autores que coincidan con la query.
* POST /coauthors/most-relevant-authors: Obtiene los autores más relevantes de un Topic.
* GET /author/{id}: Obtiene la informacion de un autor.
* GET /article/{id}: Obtiene la informacion de un artículo.
* GET /coauthors/{id}: Obtiene la lista de coautores de un autor.
* POST /articles/most-relevant-articles: Obitene la lista de artículos más relevantes de un Topic.
* GET /random-authors: Obtiene una lista aleatoria de autores 
* GET /random-topics: Obtiene una lista aleatoria de tópicos 


## Licencia
Este proyecto está bajo la Licencia MIT.