# Proyecto Final Redes de Datos
Esto repositorio aloja el proyecto final de la materia Redes de Datos de la Tecnicatura Universitaria en Inteligencia Artificial.

## Librerías
* FastAPI - versión: 0.115.8
* Uvicorn - versión: 0.34.0
* Requests - versión: 2.34.2

## Dataset

La carpeta `database/matches` no debe versionarse en Git. Para utilizar la API y el cliente primero hay que descargar el dataset de `openfootball/football.json` ejecutando:

```bash
.venv/bin/python scripts/download_openfootball_dataset.py
```

El script descarga el repositorio público y copia su estructura de dataset dentro de `database/matches`.

### Estructura

- [server/main.py](/Users/marianodorda/Documents/Personal/Facultad/TUIA/IA3.5.%20Redes%20de%20Datos/TP/server/main.py): arranque de la API, middleware y `healthcheck`.
- [server/routers/competitions.py](/Users/marianodorda/Documents/Personal/Facultad/TUIA/IA3.5.%20Redes%20de%20Datos/TP/server/routers/competitions.py): recurso `competitions`.
- [server/routers/matches.py](/Users/marianodorda/Documents/Personal/Facultad/TUIA/IA3.5.%20Redes%20de%20Datos/TP/server/routers/matches.py): recurso `matches`.
- [server/routers/rate_limit.py](/Users/marianodorda/Documents/Personal/Facultad/TUIA/IA3.5.%20Redes%20de%20Datos/TP/server/routers/rate_limit.py): recurso `rate-limit`.
- [server/schemas.py](/Users/marianodorda/Documents/Personal/Facultad/TUIA/IA3.5.%20Redes%20de%20Datos/TP/server/schemas.py): modelos Pydantic.
- [server/data_access.py](/Users/marianodorda/Documents/Personal/Facultad/TUIA/IA3.5.%20Redes%20de%20Datos/TP/server/data_access.py): lectura y escritura de JSON.
- [server/dependencies.py](/Users/marianodorda/Documents/Personal/Facultad/TUIA/IA3.5.%20Redes%20de%20Datos/TP/server/dependencies.py): autenticación Basic.
- [server/config.py](/Users/marianodorda/Documents/Personal/Facultad/TUIA/IA3.5.%20Redes%20de%20Datos/TP/server/config.py): configuración general.
- [server/rate_limit_store.py](/Users/marianodorda/Documents/Personal/Facultad/TUIA/IA3.5.%20Redes%20de%20Datos/TP/server/rate_limit_store.py): estado mutable del rate limit.
- [client/main.py](/Users/marianodorda/Documents/Personal/Facultad/TUIA/IA3.5.%20Redes%20de%20Datos/TP/client/main.py): cliente web simple.
- [client/config.py](/Users/marianodorda/Documents/Personal/Facultad/TUIA/IA3.5.%20Redes%20de%20Datos/TP/client/config.py): URL base del servidor API.
- [scripts/download_openfootball_dataset.py](/Users/marianodorda/Documents/Personal/Facultad/TUIA/IA3.5.%20Redes%20de%20Datos/TP/scripts/download_openfootball_dataset.py): descarga e instala el dataset.
- `database/matches/`: archivos JSON de competencias y partidos.

## Servidor API

La API REST expone los archivos JSON ubicados en `database/matches`.

### Ejecutar servidor

Desde la carpeta `TP/`:

```bash
.venv/bin/python -m uvicorn server.main:app --host 0.0.0.0 --port 8000 --reload
```

También se puede ejecutar con:

```bash
.venv/bin/python -m server.main
```

### Variables de entorno del servidor

```bash
export API_BASIC_USER=admin
export API_BASIC_PASSWORD=admin123
export RATE_LIMIT_REQUESTS=5
export RATE_LIMIT_WINDOW_SECONDS=1
```

### Endpoints principales

- `GET /health`
- `GET /competitions`
- `GET /competitions/{season}/{league}`
- `GET /competitions/{season}/{league}/matches`
- `GET /competitions/{season}/{league}/matches/{match_id}`
- `GET /rate-limit`
- `PUT /rate-limit`
- `POST /competitions/{season}/{league}/matches`
- `DELETE /competitions/{season}/{league}/matches/{match_id}`

### Filtros disponibles

En `GET /competitions/{season}/{league}/matches`:

- `team`
- `round`
- `date`
- `limit`
- `offset`

### Seguridad

- Los métodos `POST` y `DELETE` usan autenticación `Basic`.
- `GET /rate-limit` y `PUT /rate-limit` también usan autenticación `Basic`.
- La API aplica limitación de solicitudes en memoria por cliente y por ruta.
- El límite puede actualizarse en tiempo de ejecución usando `PUT /rate-limit`.

## Cliente web

El cliente se llama `Fútbol en el Recuerdo`. Es una web muy simple, con formularios tipo “principios de los 2000”, pensada para consumir todos los endpoints del servidor y mostrar status, headers y body de la respuesta.

Características del cliente:

- Navegación por recursos desde una barra lateral izquierda.
- Paginación visible para los listados.
- Vista previa tabular cuando la respuesta es una lista.
- Visualización del body y headers HTTP completos.

### Ejecutar cliente

Desde la carpeta `TP/`:

```bash
.venv/bin/python -m uvicorn client.main:app --host 0.0.0.0 --port 8001 --reload
```

También se puede ejecutar con:

```bash
.venv/bin/python -m client.main
```

### Variable de entorno del cliente

```bash
export SERVER_API_BASE_URL=http://127.0.0.1:8000
```

### Endpoints que consume el cliente

- `GET /health`
- `GET /competitions`
- `GET /competitions/{season}/{league}`
- `GET /competitions/{season}/{league}/matches`
- `GET /competitions/{season}/{league}/matches/{match_id}`
- `POST /competitions/{season}/{league}/matches`
- `DELETE /competitions/{season}/{league}/matches/{match_id}`
- `GET /rate-limit`
- `PUT /rate-limit`

## Paginación

Los endpoints de listado usan paginación por `limit` y `offset`:

- `GET /competitions`
- `GET /competitions/{season}/{league}/matches`

Además, el servidor devuelve encabezados útiles para la interfaz:

- `X-Total-Count`
- `X-Limit`
- `X-Offset`

### Estructura de datos

Cada archivo JSON representa una competencia y tiene esta forma general:

```json
{
  "name": "English Premier League 2024/25",
  "matches": [
    {
      "round": "Matchday 1",
      "date": "2024-08-16",
      "time": "20:00",
      "team1": "Manchester United FC",
      "team2": "Fulham FC",
      "score": {
        "ht": [0, 0],
        "ft": [1, 0]
      }
    }
  ]
}
```
