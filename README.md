# Proyecto Final Redes de Datos
Esto repositorio aloja el proyecto final de la materia Redes de Datos de la Tecnicatura Universitaria en Inteligencia Artificial.

## Librerias
* FastAPI - versión: 0.115.8
* Uvicorn - versión: 0.34.0

## Servidor API

El servidor está implementado en [main.py](/Users/marianodorda/Documents/Personal/Facultad/TUIA/IA3.5.%20Redes%20de%20Datos/TP/main.py) y expone una API REST sobre los archivos JSON ubicados en `database/matches`.

### Estructura

- [main.py](/Users/marianodorda/Documents/Personal/Facultad/TUIA/IA3.5.%20Redes%20de%20Datos/TP/main.py): arranque de la app, middleware y `healthcheck`.
- [routers/competitions.py](/Users/marianodorda/Documents/Personal/Facultad/TUIA/IA3.5.%20Redes%20de%20Datos/TP/routers/competitions.py): recurso `competitions`.
- [routers/matches.py](/Users/marianodorda/Documents/Personal/Facultad/TUIA/IA3.5.%20Redes%20de%20Datos/TP/routers/matches.py): recurso `matches`.
- [routers/rate_limit.py](/Users/marianodorda/Documents/Personal/Facultad/TUIA/IA3.5.%20Redes%20de%20Datos/TP/routers/rate_limit.py): recurso `rate-limit`.
- [schemas.py](/Users/marianodorda/Documents/Personal/Facultad/TUIA/IA3.5.%20Redes%20de%20Datos/TP/schemas.py): modelos Pydantic.
- [data_access.py](/Users/marianodorda/Documents/Personal/Facultad/TUIA/IA3.5.%20Redes%20de%20Datos/TP/data_access.py): lectura y escritura de JSON.
- [dependencies.py](/Users/marianodorda/Documents/Personal/Facultad/TUIA/IA3.5.%20Redes%20de%20Datos/TP/dependencies.py): autenticación Basic.
- [config.py](/Users/marianodorda/Documents/Personal/Facultad/TUIA/IA3.5.%20Redes%20de%20Datos/TP/config.py): configuración general.
- [rate_limit_store.py](/Users/marianodorda/Documents/Personal/Facultad/TUIA/IA3.5.%20Redes%20de%20Datos/TP/rate_limit_store.py): estado mutable del rate limit.

### Ejecutar

Desde la carpeta `TP/`:

```bash
.venv/bin/python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

También se puede ejecutar con:

```bash
.venv/bin/python main.py
```

### Variables de entorno

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
