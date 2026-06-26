# Proyecto Final Redes de Datos
Esto repositorio aloja el proyecto final de la materia Redes de Datos de la Tecnicatura Universitaria en Inteligencia Artificial.

## Librerias
* FastAPI - versión: 0.115.8
* Uvicorn - versión: 0.34.0

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
