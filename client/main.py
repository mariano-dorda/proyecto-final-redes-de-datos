import html
import json
import re

import requests
import uvicorn
from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from .config import SERVER_API_BASE_URL


APP_NAME = "Fútbol en el Recuerdo"
COOKIE_API_BASE_URL = "api_base_url"
COOKIE_USERNAME = "api_username"
COOKIE_PASSWORD = "api_password"
DEFAULT_PAGE_SIZE = 20

app = FastAPI(
    title=APP_NAME,
    description="Cliente web retro para consumir la API de partidos.",
    version="4.0.0",
)

SIDEBAR_ITEMS = [
    ("/competitions", "Competiciones"),
    ("/competition-detail", "Competición"),
    ("/matches", "Partidos"),
    ("/match-detail", "Partido"),
    ("/match-create", "Agregar Partido"),
    ("/match-update", "Modificar Partido"),
    ("/match-delete", "Quitar Partido"),
    ("/rate-limit", "Límite de velocidad"),
    ("/rate-limit-update", "Modificar Límite de velocidad"),
    ("/health", "Salud de la API"),
]

FIELD_LABELS = {
    "season": "Temporada",
    "league": "Liga",
    "name": "Nombre",
    "matches_count": "Cantidad de Partidos",
    "match_id": "ID del Partido",
    "round": "Ronda",
    "date": "Fecha",
    "time": "Hora",
    "team": "Equipo",
    "team1": "Equipo Local",
    "team2": "Equipo Visitante",
    "score": "Marcador",
    "ht": "Marcador Primera Mitad",
    "ft": "Marcador Final",
    "requests": "Solicitudes",
    "window_seconds": "Ventana (segundos)",
    "status": "Estado",
    "database_dir": "Directorio de Base de Datos",
    "rate_limit_requests": "Solicitudes por Ventana",
    "rate_limit_window_seconds": "Ventana de Tiempo",
    "ht_score": "Marcador Primera Mitad",
    "ft_score": "Marcador Final",
}


def get_client_settings(request: Request) -> dict[str, str]:
    return {
        "api_base_url": request.cookies.get(COOKIE_API_BASE_URL, SERVER_API_BASE_URL),
        "username": request.cookies.get(COOKIE_USERNAME, "admin"),
        "password": request.cookies.get(COOKIE_PASSWORD, "admin123"),
    }


def render_sidebar(current_path: str) -> str:
    links = []
    for href, label in SIDEBAR_ITEMS:
        active_style = " style='background:#efe6d5;font-weight:bold;'" if href == current_path else ""
        links.append(f'<a href="{href}"{active_style}>{html.escape(label)}</a>')
    return "".join(links)


def render_settings_bar(settings: dict[str, str]) -> str:
    return f"""
    <div class="settings-bar">
      <form method="post" action="/settings">
        <div class="settings-grid">
          <div><label>API base URL</label><input name="api_base_url" value="{html.escape(settings['api_base_url'])}"></div>
          <div><label>Usuario</label><input name="username" value="{html.escape(settings['username'])}"></div>
          <div><label>Password</label><input name="password" type="password" value="{html.escape(settings['password'])}"></div>
          <div><input class="button" type="submit" value="Guardar configuración"></div>
        </div>
      </form>
    </div>
    """


def render_layout(
    *,
    current_path: str,
    page_title: str,
    form_html: str,
    settings: dict[str, str],
    result_html: str = "",
) -> str:
    return f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>{APP_NAME}</title>
  <style>
    body {{ margin: 0; padding: 0; background: #d7d7d7; color: #111; font-family: Verdana, Geneva, sans-serif; }}
    .wrapper {{ width: 1240px; margin: 0 auto; background: #f3f0e8; border-left: 1px solid #8f8f8f; border-right: 1px solid #8f8f8f; min-height: 100vh; }}
    .topbar {{ background: #133c67; color: #fff7d4; padding: 14px 18px; border-bottom: 3px solid #7a9fbe; }}
    .topbar h1 {{ margin: 0; font-size: 28px; }}
    .settings-bar {{ background: #d8deea; border-bottom: 1px solid #8f8f8f; padding: 10px 18px; }}
    .settings-grid {{ display: grid; grid-template-columns: 1.6fr 1fr 1fr auto; gap: 12px; align-items: end; }}
    .settings-grid label {{ display: block; font-size: 12px; margin-bottom: 4px; }}
    .settings-grid input {{ width: 100%; box-sizing: border-box; }}
    .main {{ display: flex; align-items: flex-start; }}
    .sidebar {{ width: 220px; background: #e0d7c8; border-right: 1px solid #9b927f; min-height: calc(100vh - 120px); padding: 16px 12px; box-sizing: border-box; }}
    .sidebar a {{ display: block; color: #0b3470; text-decoration: none; font-size: 13px; padding: 6px 4px; border-bottom: 1px dotted #b8aa93; }}
    .sidebar a:hover {{ background: #efe6d5; }}
    .content {{ flex: 1; padding: 16px 18px 28px; box-sizing: border-box; }}
    .box {{ border: 1px solid #8f8f8f; background: #faf8f1; margin: 0 0 16px; }}
    .box h2 {{ margin: 0; padding: 8px 10px; background: #d6dce5; border-bottom: 1px solid #8f8f8f; font-size: 16px; }}
    .box-body {{ padding: 10px; }}
    .row {{ margin: 7px 0; }}
    label {{ display: inline-block; width: 180px; vertical-align: top; font-size: 13px; }}
    input {{ width: 320px; font-family: "Courier New", monospace; font-size: 13px; padding: 3px; border: 1px solid #7f7f7f; background: #fff; }}
    .small {{ width: 90px; }}
    .button {{ width: auto; padding: 4px 10px; font-family: Verdana, Geneva, sans-serif; background: #dcdcdc; border: 1px solid #666; cursor: pointer; }}
    .button:hover {{ background: #ececec; }}
    .hint {{ font-size: 12px; color: #555; }}
    pre {{ background: #fff; border: 1px solid #8f8f8f; padding: 10px; overflow-x: auto; font-size: 12px; }}
    table {{ width: 100%; border-collapse: collapse; background: #fff; margin-bottom: 12px; }}
    th, td {{ border: 1px solid #8f8f8f; padding: 6px; font-size: 12px; text-align: left; vertical-align: top; }}
    th {{ background: #ece6d6; }}
    .result-title {{ color: #593e1a; font-size: 18px; margin: 0 0 10px; }}
    .inline-form {{ display: inline-block; margin-right: 8px; }}
    .pager {{ margin: 10px 0 0; padding: 8px; background: #ebe6db; border: 1px solid #b2aa9d; }}
    .pager span {{ font-size: 12px; margin-right: 12px; }}
    .page-title {{ margin: 0 0 14px; font-size: 24px; color: #593e1a; }}
    .friendly-grid {{ display: grid; grid-template-columns: 220px 1fr; gap: 6px 10px; background: #fff; border: 1px solid #8f8f8f; padding: 10px; margin-bottom: 12px; font-size: 13px; }}
    .friendly-grid strong {{ color: #593e1a; }}
    details {{ margin-top: 12px; }}
    summary {{ cursor: pointer; font-weight: bold; color: #133c67; }}
  </style>
</head>
<body>
  <div class="wrapper">
    <div class="topbar"><h1>{APP_NAME}</h1></div>
    {render_settings_bar(settings)}
    <div class="main">
      <div class="sidebar">{render_sidebar(current_path)}</div>
      <div class="content">
        <h2 class="page-title">{html.escape(page_title)}</h2>
        {result_html}
        {form_html}
      </div>
    </div>
  </div>
</body>
</html>"""


def render_form_box(title: str, action: str, body_html: str) -> str:
    return f'<div class="box"><h2>{html.escape(title)}</h2><div class="box-body"><form method="post" action="{html.escape(action)}">{body_html}</form></div></div>'


def build_hidden_inputs(values: dict[str, str | int]) -> str:
    return "".join(
        f'<input type="hidden" name="{html.escape(str(key))}" value="{html.escape(str(value))}">'
        for key, value in values.items()
    )


def build_table_preview(data: object) -> str:
    if not isinstance(data, list) or not data or not isinstance(data[0], dict):
        return ""
    normalized_items = [normalize_item(item) for item in data[:20]]
    columns = order_columns(list(normalized_items[0].keys()))[:8]
    header = "".join(f"<th>{html.escape(FIELD_LABELS.get(str(column), str(column)))}</th>" for column in columns)
    rows = []
    for item in normalized_items:
        row = "".join(
            f"<td>{html.escape(format_simple_value(item.get(column)))}</td>"
            for column in columns
        )
        rows.append(f"<tr>{row}</tr>")
    return f"<table><tr>{header}</tr>{''.join(rows)}</table>"


def normalize_item(item: dict) -> dict:
    normalized = dict(item)
    if "round" in normalized:
        normalized["round"] = simplify_round(normalized["round"])
    score = normalized.pop("score", None)
    if isinstance(score, dict):
        ht = score.get("ht", [])
        ft = score.get("ft", [])
        normalized["ht_score"] = format_score_pair(ht)
        normalized["ft_score"] = format_score_pair(ft)
    return normalized


def format_score_pair(values: list) -> str:
    home = values[0] if len(values) > 0 else "-"
    away = values[1] if len(values) > 1 else "-"
    return f"{home} - {away}"


def simplify_round(value) -> str:
    text = str(value)
    match = re.search(r"(\d+)$", text)
    return match.group(1) if match else text


def order_columns(columns: list[str]) -> list[str]:
    ordered = list(columns)
    if "match_id" in ordered:
        ordered.insert(0, ordered.pop(ordered.index("match_id")))
    return ordered


def format_simple_value(value) -> str:
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False)
    return str(value)


def build_friendly_body(data: object) -> str:
    if isinstance(data, list):
        return build_table_preview(data)
    if isinstance(data, dict):
        normalized = normalize_item(data)
        if "matches" in normalized and isinstance(normalized["matches"], list):
            normalized.pop("matches")
        rows = []
        for key, value in normalized.items():
            label = FIELD_LABELS.get(str(key), str(key))
            rows.append(f"<strong>{html.escape(label)}</strong><span>{html.escape(format_simple_value(value))}</span>")
        return f'<div class="friendly-grid">{"".join(rows)}</div>'
    return ""


def build_pagination_html(
    *,
    action: str,
    total_count: int,
    limit: int,
    offset: int,
    hidden_fields: dict[str, str | int],
) -> str:
    start = offset + 1 if total_count > 0 else 0
    end = min(offset + limit, total_count)
    previous_offset = max(offset - limit, 0)
    next_offset = offset + limit
    prev_form = ""
    if offset > 0:
        prev_fields = dict(hidden_fields)
        prev_fields["offset"] = previous_offset
        prev_form = f'<form class="inline-form" method="post" action="{html.escape(action)}">{build_hidden_inputs(prev_fields)}<input class="button" type="submit" value="Anterior"></form>'
    next_form = ""
    if next_offset < total_count:
        next_fields = dict(hidden_fields)
        next_fields["offset"] = next_offset
        next_form = f'<form class="inline-form" method="post" action="{html.escape(action)}">{build_hidden_inputs(next_fields)}<input class="button" type="submit" value="Siguiente"></form>'
    return f'<div class="pager"><span>Mostrando {start} a {end} de {total_count} resultado(s).</span>{prev_form}{next_form}</div>'


def build_result_html(*, method: str, url: str, response: requests.Response, body: str | None = None, pagination_html: str = "", success_message: str = "") -> str:
    headers_text = "\n".join(f"{k}: {v}" for k, v in response.headers.items())
    try:
        response_json = response.json()
        response_text = json.dumps(response_json, ensure_ascii=False, indent=2)
        preview_html = build_friendly_body(response_json)
    except ValueError:
        response_text = response.text
        preview_html = ""
    request_body = body if body else "(sin body)"
    return (
        f'<div class="box"><h2>Resultado</h2><div class="box-body"><div class="result-title">{html.escape(method)} {html.escape(url)}</div>'
        f'<p><strong>Status:</strong> {response.status_code}</p>'
        f'{f"<p><strong>{html.escape(success_message)}</strong></p>" if success_message else ""}'
        f'{pagination_html}{preview_html}'
        f'<details><summary>Ver detalles técnicos de la respuesta</summary>'
        f'<p><strong>Request body:</strong></p><pre>{html.escape(request_body)}</pre>'
        f'<p><strong>Response headers:</strong></p><pre>{html.escape(headers_text)}</pre>'
        f'<p><strong>Response body:</strong></p><pre>{html.escape(response_text)}</pre>'
        f'</details></div></div>'
    )


def perform_request(*, method: str, api_base_url: str, path: str, params: dict | None = None, json_body: dict | None = None, username: str | None = None, password: str | None = None) -> requests.Response:
    auth = (username, password) if username and password else None
    return requests.request(method=method, url=api_base_url.rstrip("/") + path, params={k: v for k, v in (params or {}).items() if v not in ("", None)}, json=json_body, auth=auth, timeout=10)


def form_health() -> str:
    return render_form_box("GET /health", "/health", '<div class="row"><input class="button" type="submit" value="Consultar health"></div>')


def form_competitions() -> str:
    return render_form_box("GET /competitions", "/competitions", '<div class="row"><label>Temporada</label><input name="season"></div><div class="row"><label>Liga</label><input name="league"></div><input type="hidden" name="offset" value="0"><div class="row"><span class="hint">La paginación se maneja automáticamente con los botones de navegación.</span></div><div class="row"><input class="button" type="submit" value="Listar Competiciones"></div>')


def form_competition_detail() -> str:
    return render_form_box("GET /competitions/{season}/{league}", "/competition-detail", '<div class="row"><label>Temporada</label><input name="season" value="2024-25"></div><div class="row"><label>Liga</label><input name="league" value="en.1"></div><div class="row"><input class="button" type="submit" value="Ver Competición"></div>')


def form_matches() -> str:
    return render_form_box("GET /competitions/{season}/{league}/matches", "/matches", '<div class="row"><label>Temporada</label><input name="season" value="2024-25"></div><div class="row"><label>Liga</label><input name="league" value="en.1"></div><div class="row"><label>Equipo</label><input name="team"></div><div class="row"><label>Ronda</label><input name="round_name"></div><div class="row"><label>Fecha</label><input name="date"></div><input type="hidden" name="offset" value="0"><div class="row"><input class="button" type="submit" value="Listar Partidos"></div>')


def form_match_detail() -> str:
    return render_form_box("GET /competitions/{season}/{league}/matches/{match_id}", "/match-detail", '<div class="row"><label>Temporada</label><input name="season" value="2024-25"></div><div class="row"><label>Liga</label><input name="league" value="en.1"></div><div class="row"><label>ID del Partido</label><input class="small" name="match_id" value="0"></div><div class="row"><input class="button" type="submit" value="Ver Partido"></div>')


def form_match_create() -> str:
    return render_form_box("POST /competitions/{season}/{league}/matches", "/match-create", '<div class="row"><label>Temporada</label><input name="season" value="2025"></div><div class="row"><label>Liga</label><input name="league" value="mls"></div><div class="row"><label>Ronda</label><input name="round" value="Matchday X"></div><div class="row"><label>Fecha</label><input name="date" value="2099-01-01"></div><div class="row"><label>Hora</label><input name="time" value="20:00"></div><div class="row"><label>Equipo Local</label><input name="team1" value="Equipo A"></div><div class="row"><label>Equipo Visitante</label><input name="team2" value="Equipo B"></div><div class="row"><label>Marcador Primera Mitad</label><input class="small" name="ht_home" value="0"> <input class="small" name="ht_away" value="0"></div><div class="row"><label>Marcador Final</label><input class="small" name="ft_home" value="1"> <input class="small" name="ft_away" value="0"></div><div class="row"><input class="button" type="submit" value="Agregar Partido"></div>')


def form_match_delete() -> str:
    return render_form_box("DELETE /competitions/{season}/{league}/matches/{match_id}", "/match-delete", '<div class="row"><label>Temporada</label><input name="season" value="2025"></div><div class="row"><label>Liga</label><input name="league" value="mls"></div><div class="row"><label>ID del Partido</label><input class="small" name="match_id" value="0"></div><div class="row"><input class="button" type="submit" value="Quitar Partido"></div>')


def form_match_update() -> str:
    return render_form_box("PUT /competitions/{season}/{league}/matches/{match_id}", "/match-update", '<div class="row"><label>Temporada</label><input name="season" value="2025"></div><div class="row"><label>Liga</label><input name="league" value="mls"></div><div class="row"><label>ID del Partido</label><input class="small" name="match_id" value="0"></div><div class="row"><label>Ronda</label><input name="round" placeholder="Opcional"></div><div class="row"><label>Fecha</label><input name="date" placeholder="Opcional"></div><div class="row"><label>Hora</label><input name="time" placeholder="Opcional"></div><div class="row"><label>Equipo Local</label><input name="team1" placeholder="Opcional"></div><div class="row"><label>Equipo Visitante</label><input name="team2" placeholder="Opcional"></div><div class="row"><label>Marcador Primera Mitad</label><input class="small" name="ht_home" placeholder="Opcional"> <input class="small" name="ht_away" placeholder="Opcional"></div><div class="row"><label>Marcador Final</label><input class="small" name="ft_home" placeholder="Opcional"> <input class="small" name="ft_away" placeholder="Opcional"></div><div class="row"><span class="hint">Solo se actualizan los campos que se completen. Si modificás un marcador, cargá ambos goles del bloque.</span></div><div class="row"><input class="button" type="submit" value="Modificar Partido"></div>')


def form_rate_limit_get() -> str:
    return render_form_box("GET /rate-limit", "/rate-limit", '<div class="row"><input class="button" type="submit" value="Ver Límite de velocidad"></div>')


def form_rate_limit_update() -> str:
    return render_form_box("PUT /rate-limit", "/rate-limit-update", '<div class="row"><label>Solicitudes</label><input class="small" name="requests_limit" value="5"></div><div class="row"><label>Ventana (segundos)</label><input class="small" name="window_seconds" value="1"></div><div class="row"><input class="button" type="submit" value="Modificar Límite de velocidad"></div>')


def render_page(current_path: str, page_title: str, form_html: str, request: Request, result_html: str = "") -> HTMLResponse:
    return HTMLResponse(render_layout(current_path=current_path, page_title=page_title, form_html=form_html, settings=get_client_settings(request), result_html=result_html))


def render_error(current_path: str, page_title: str, form_html: str, request: Request, message: str) -> HTMLResponse:
    return render_page(current_path, page_title, form_html, request, f'<div class="box"><h2>Error</h2><div class="box-body"><pre>{html.escape(message)}</pre></div></div>')


def maybe_parse_score_pair(home_value: str, away_value: str, label: str) -> tuple[list[int] | None, str | None]:
    if home_value == "" and away_value == "":
        return None, None
    if home_value == "" or away_value == "":
        return None, f"Para modificar {label} tenés que completar ambos goles."
    return [int(home_value), int(away_value)], None


@app.get("/", response_class=HTMLResponse)
def home():
    return RedirectResponse(url="/health", status_code=302)


@app.post("/settings")
def save_settings(
    api_base_url: str = Form(...),
    username: str = Form(...),
    password: str = Form(...),
):
    response = RedirectResponse(url="/health", status_code=303)
    response.set_cookie(COOKIE_API_BASE_URL, api_base_url)
    response.set_cookie(COOKIE_USERNAME, username)
    response.set_cookie(COOKIE_PASSWORD, password)
    return response


@app.get("/health", response_class=HTMLResponse)
def health_page(request: Request):
    settings = get_client_settings(request)
    form_html = form_health()
    try:
        response = perform_request(method="GET", api_base_url=settings["api_base_url"], path="/health")
        result = build_result_html(method="GET", url=f'{settings["api_base_url"].rstrip("/")}/health', response=response)
    except requests.RequestException as exc:
        result = f'<div class="box"><h2>Error</h2><div class="box-body"><pre>{html.escape(str(exc))}</pre></div></div>'
    return render_page("/health", "Salud de la API", form_html, request, result)


@app.post("/health", response_class=HTMLResponse)
def health_action(request: Request):
    settings = get_client_settings(request)
    form_html = form_health()
    try:
        response = perform_request(method="GET", api_base_url=settings["api_base_url"], path="/health")
    except requests.RequestException as exc:
        return render_error("/health", "Salud de la API", form_html, request, str(exc))
    result = build_result_html(method="GET", url=f'{settings["api_base_url"].rstrip("/")}/health', response=response)
    return render_page("/health", "Salud de la API", form_html, request, result)


@app.get("/competitions", response_class=HTMLResponse)
def competitions_page(request: Request):
    return render_page("/competitions", "Competiciones", form_competitions(), request)


@app.post("/competitions", response_class=HTMLResponse)
def competitions_action(request: Request, season: str = Form(""), league: str = Form(""), offset: int = Form(0)):
    settings = get_client_settings(request)
    form_html = form_competitions()
    try:
        response = perform_request(method="GET", api_base_url=settings["api_base_url"], path="/competitions", params={"season": season, "league": league, "limit": DEFAULT_PAGE_SIZE, "offset": offset})
    except requests.RequestException as exc:
        return render_error("/competitions", "Competiciones", form_html, request, str(exc))
    total_count = int(response.headers.get("X-Total-Count", "0"))
    pagination_html = build_pagination_html(action="/competitions", total_count=total_count, limit=DEFAULT_PAGE_SIZE, offset=offset, hidden_fields={"season": season, "league": league})
    result = build_result_html(method="GET", url=f'{settings["api_base_url"].rstrip("/")}/competitions', response=response, pagination_html=pagination_html)
    return render_page("/competitions", "Competiciones", form_html, request, result)


@app.get("/competition-detail", response_class=HTMLResponse)
def competition_detail_page(request: Request):
    return render_page("/competition-detail", "Competición", form_competition_detail(), request)


@app.post("/competition-detail", response_class=HTMLResponse)
def competition_detail_action(request: Request, season: str = Form(...), league: str = Form(...)):
    settings = get_client_settings(request)
    form_html = form_competition_detail()
    path = f"/competitions/{season}/{league}"
    try:
        response = perform_request(method="GET", api_base_url=settings["api_base_url"], path=path)
    except requests.RequestException as exc:
        return render_error("/competition-detail", "Competición", form_html, request, str(exc))
    result = build_result_html(method="GET", url=f'{settings["api_base_url"].rstrip("/")}{path}', response=response)
    return render_page("/competition-detail", "Competición", form_html, request, result)


@app.get("/matches", response_class=HTMLResponse)
def matches_page(request: Request):
    return render_page("/matches", "Partidos", form_matches(), request)


@app.post("/matches", response_class=HTMLResponse)
def matches_action(request: Request, season: str = Form(...), league: str = Form(...), team: str = Form(""), round_name: str = Form(""), date: str = Form(""), offset: int = Form(0)):
    settings = get_client_settings(request)
    form_html = form_matches()
    path = f"/competitions/{season}/{league}/matches"
    try:
        response = perform_request(method="GET", api_base_url=settings["api_base_url"], path=path, params={"team": team, "round": round_name, "date": date, "limit": DEFAULT_PAGE_SIZE, "offset": offset})
    except requests.RequestException as exc:
        return render_error("/matches", "Partidos", form_html, request, str(exc))
    total_count = int(response.headers.get("X-Total-Count", "0"))
    pagination_html = build_pagination_html(action="/matches", total_count=total_count, limit=DEFAULT_PAGE_SIZE, offset=offset, hidden_fields={"season": season, "league": league, "team": team, "round_name": round_name, "date": date})
    result = build_result_html(method="GET", url=f'{settings["api_base_url"].rstrip("/")}{path}', response=response, pagination_html=pagination_html)
    return render_page("/matches", "Partidos", form_html, request, result)


@app.get("/match-detail", response_class=HTMLResponse)
def match_detail_page(request: Request):
    return render_page("/match-detail", "Partido", form_match_detail(), request)


@app.post("/match-detail", response_class=HTMLResponse)
def match_detail_action(request: Request, season: str = Form(...), league: str = Form(...), match_id: int = Form(...)):
    settings = get_client_settings(request)
    form_html = form_match_detail()
    path = f"/competitions/{season}/{league}/matches/{match_id}"
    try:
        response = perform_request(method="GET", api_base_url=settings["api_base_url"], path=path)
    except requests.RequestException as exc:
        return render_error("/match-detail", "Partido", form_html, request, str(exc))
    result = build_result_html(method="GET", url=f'{settings["api_base_url"].rstrip("/")}{path}', response=response)
    return render_page("/match-detail", "Partido", form_html, request, result)


@app.get("/match-create", response_class=HTMLResponse)
def match_create_page(request: Request):
    return render_page("/match-create", "Agregar Partido", form_match_create(), request)


@app.post("/match-create", response_class=HTMLResponse)
def match_create_action(request: Request, season: str = Form(...), league: str = Form(...), round: str = Form(...), date: str = Form(...), time_value: str = Form(..., alias="time"), team1: str = Form(...), team2: str = Form(...), ht_home: int = Form(...), ht_away: int = Form(...), ft_home: int = Form(...), ft_away: int = Form(...)):
    settings = get_client_settings(request)
    form_html = form_match_create()
    path = f"/competitions/{season}/{league}/matches"
    payload = {"round": round, "date": date, "time": time_value, "team1": team1, "team2": team2, "score": {"ht": [ht_home, ht_away], "ft": [ft_home, ft_away]}}
    try:
        response = perform_request(method="POST", api_base_url=settings["api_base_url"], path=path, json_body=payload, username=settings["username"], password=settings["password"])
    except requests.RequestException as exc:
        return render_error("/match-create", "Agregar Partido", form_html, request, str(exc))
    result = build_result_html(method="POST", url=f'{settings["api_base_url"].rstrip("/")}{path}', response=response, body=json.dumps(payload, ensure_ascii=False, indent=2))
    return render_page("/match-create", "Agregar Partido", form_html, request, result)


@app.get("/match-delete", response_class=HTMLResponse)
def match_delete_page(request: Request):
    return render_page("/match-delete", "Quitar Partido", form_match_delete(), request)


@app.post("/match-delete", response_class=HTMLResponse)
def match_delete_action(request: Request, season: str = Form(...), league: str = Form(...), match_id: int = Form(...)):
    settings = get_client_settings(request)
    form_html = form_match_delete()
    path = f"/competitions/{season}/{league}/matches/{match_id}"
    try:
        response = perform_request(method="DELETE", api_base_url=settings["api_base_url"], path=path, username=settings["username"], password=settings["password"])
    except requests.RequestException as exc:
        return render_error("/match-delete", "Quitar Partido", form_html, request, str(exc))
    success_message = ""
    if response.status_code == 204:
        success_message = f"El partido con ID {match_id} fue eliminado correctamente."
    result = build_result_html(method="DELETE", url=f'{settings["api_base_url"].rstrip("/")}{path}', response=response, success_message=success_message)
    return render_page("/match-delete", "Quitar Partido", form_html, request, result)


@app.get("/match-update", response_class=HTMLResponse)
def match_update_page(request: Request):
    return render_page("/match-update", "Modificar Partido", form_match_update(), request)


@app.post("/match-update", response_class=HTMLResponse)
def match_update_action(request: Request, season: str = Form(...), league: str = Form(...), match_id: int = Form(...), round: str = Form(""), date: str = Form(""), time_value: str = Form("", alias="time"), team1: str = Form(""), team2: str = Form(""), ht_home: str = Form(""), ht_away: str = Form(""), ft_home: str = Form(""), ft_away: str = Form("")):
    settings = get_client_settings(request)
    form_html = form_match_update()
    path = f"/competitions/{season}/{league}/matches/{match_id}"
    ht_score, ht_error = maybe_parse_score_pair(ht_home, ht_away, "el Marcador Primera Mitad")
    if ht_error:
        return render_error("/match-update", "Modificar Partido", form_html, request, ht_error)
    ft_score, ft_error = maybe_parse_score_pair(ft_home, ft_away, "el Marcador Final")
    if ft_error:
        return render_error("/match-update", "Modificar Partido", form_html, request, ft_error)

    payload = {}
    if round:
        payload["round"] = round
    if date:
        payload["date"] = date
    if time_value:
        payload["time"] = time_value
    if team1:
        payload["team1"] = team1
    if team2:
        payload["team2"] = team2
    score_payload = {}
    if ht_score is not None:
        score_payload["ht"] = ht_score
    if ft_score is not None:
        score_payload["ft"] = ft_score
    if score_payload:
        payload["score"] = score_payload

    if not payload:
        return render_error("/match-update", "Modificar Partido", form_html, request, "Completá al menos un campo para modificar.")

    try:
        response = perform_request(method="PUT", api_base_url=settings["api_base_url"], path=path, json_body=payload, username=settings["username"], password=settings["password"])
    except requests.RequestException as exc:
        return render_error("/match-update", "Modificar Partido", form_html, request, str(exc))
    result = build_result_html(method="PUT", url=f'{settings["api_base_url"].rstrip("/")}{path}', response=response, body=json.dumps(payload, ensure_ascii=False, indent=2))
    return render_page("/match-update", "Modificar Partido", form_html, request, result)


@app.get("/rate-limit", response_class=HTMLResponse)
def rate_limit_page(request: Request):
    settings = get_client_settings(request)
    form_html = form_rate_limit_get()
    path = "/rate-limit"
    try:
        response = perform_request(method="GET", api_base_url=settings["api_base_url"], path=path, username=settings["username"], password=settings["password"])
        result = build_result_html(method="GET", url=f'{settings["api_base_url"].rstrip("/")}{path}', response=response)
    except requests.RequestException as exc:
        result = f'<div class="box"><h2>Error</h2><div class="box-body"><pre>{html.escape(str(exc))}</pre></div></div>'
    return render_page("/rate-limit", "Límite de velocidad", form_html, request, result)


@app.post("/rate-limit", response_class=HTMLResponse)
def rate_limit_action(request: Request):
    settings = get_client_settings(request)
    form_html = form_rate_limit_get()
    path = "/rate-limit"
    try:
        response = perform_request(method="GET", api_base_url=settings["api_base_url"], path=path, username=settings["username"], password=settings["password"])
    except requests.RequestException as exc:
        return render_error("/rate-limit", "Límite de velocidad", form_html, request, str(exc))
    result = build_result_html(method="GET", url=f'{settings["api_base_url"].rstrip("/")}{path}', response=response)
    return render_page("/rate-limit", "Límite de velocidad", form_html, request, result)


@app.get("/rate-limit-update", response_class=HTMLResponse)
def rate_limit_update_page(request: Request):
    return render_page("/rate-limit-update", "Modificar Límite de velocidad", form_rate_limit_update(), request)


@app.post("/rate-limit-update", response_class=HTMLResponse)
def rate_limit_update_action(request: Request, requests_limit: int = Form(...), window_seconds: float = Form(...)):
    settings = get_client_settings(request)
    form_html = form_rate_limit_update()
    path = "/rate-limit"
    payload = {"requests": requests_limit, "window_seconds": window_seconds}
    try:
        response = perform_request(method="PUT", api_base_url=settings["api_base_url"], path=path, json_body=payload, username=settings["username"], password=settings["password"])
    except requests.RequestException as exc:
        return render_error("/rate-limit-update", "Modificar Límite de velocidad", form_html, request, str(exc))
    result = build_result_html(method="PUT", url=f'{settings["api_base_url"].rstrip("/")}{path}', response=response, body=json.dumps(payload, ensure_ascii=False, indent=2))
    return render_page("/rate-limit-update", "Modificar Límite de velocidad", form_html, request, result)


if __name__ == "__main__":
    uvicorn.run("client.main:app", host="0.0.0.0", port=8001, reload=True)
