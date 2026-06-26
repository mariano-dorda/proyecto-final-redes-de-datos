import html
import json

import requests
import uvicorn
from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse, RedirectResponse

from .config import SERVER_API_BASE_URL


APP_NAME = "Fútbol en el Recuerdo"

app = FastAPI(
    title=APP_NAME,
    description="Cliente web retro para consumir la API de partidos.",
    version="3.0.0",
)

SIDEBAR_ITEMS = [
    ("/health", "Health"),
    ("/competitions", "Competitions"),
    ("/competition-detail", "Competition detail"),
    ("/matches", "Matches"),
    ("/match-detail", "Match detail"),
    ("/match-create", "Crear match"),
    ("/match-delete", "Borrar match"),
    ("/rate-limit", "Ver rate limit"),
    ("/rate-limit-update", "Actualizar rate limit"),
]


def render_sidebar(current_path: str) -> str:
    links = []
    for href, label in SIDEBAR_ITEMS:
        active_style = " style='background:#efe6d5;font-weight:bold;'" if href == current_path else ""
        links.append(f'<a href="{href}"{active_style}>{html.escape(label)}</a>')
    return "".join(links)


def render_layout(*, current_path: str, page_title: str, form_html: str, result_html: str = "") -> str:
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
    .main {{ display: flex; align-items: flex-start; }}
    .sidebar {{ width: 220px; background: #e0d7c8; border-right: 1px solid #9b927f; min-height: calc(100vh - 61px); padding: 16px 12px; box-sizing: border-box; }}
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
  </style>
</head>
<body>
  <div class="wrapper">
    <div class="topbar">
      <h1>{APP_NAME}</h1>
    </div>
    <div class="main">
      <div class="sidebar">
        {render_sidebar(current_path)}
      </div>
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
    return f"""
    <div class="box">
      <h2>{html.escape(title)}</h2>
      <div class="box-body">
        <form method="post" action="{html.escape(action)}">
          {body_html}
        </form>
      </div>
    </div>
    """


def base_url_field(value: str | None = None) -> str:
    return f'<div class="row"><label>API base URL</label><input name="api_base_url" value="{html.escape(value or SERVER_API_BASE_URL)}"></div>'


def build_hidden_inputs(values: dict[str, str | int]) -> str:
    return "".join(
        f'<input type="hidden" name="{html.escape(str(key))}" value="{html.escape(str(value))}">'
        for key, value in values.items()
    )


def build_table_preview(data: object) -> str:
    if not isinstance(data, list) or not data or not isinstance(data[0], dict):
        return ""
    columns = list(data[0].keys())[:6]
    header = "".join(f"<th>{html.escape(str(column))}</th>" for column in columns)
    rows = []
    for item in data[:20]:
        row = "".join(
            f"<td>{html.escape(json.dumps(item.get(column), ensure_ascii=False) if isinstance(item.get(column), (dict, list)) else str(item.get(column)))}</td>"
            for column in columns
        )
        rows.append(f"<tr>{row}</tr>")
    return f"<table><tr>{header}</tr>{''.join(rows)}</table>"


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
        prev_form = (
            f'<form class="inline-form" method="post" action="{html.escape(action)}">'
            f"{build_hidden_inputs(prev_fields)}"
            '<input class="button" type="submit" value="Anterior">'
            "</form>"
        )

    next_form = ""
    if next_offset < total_count:
        next_fields = dict(hidden_fields)
        next_fields["offset"] = next_offset
        next_form = (
            f'<form class="inline-form" method="post" action="{html.escape(action)}">'
            f"{build_hidden_inputs(next_fields)}"
            '<input class="button" type="submit" value="Siguiente">'
            "</form>"
        )

    return (
        '<div class="pager">'
        f"<span>Mostrando {start} a {end} de {total_count} resultado(s).</span>"
        f"{prev_form}{next_form}"
        "</div>"
    )


def build_result_html(
    *,
    method: str,
    url: str,
    response: requests.Response,
    body: str | None = None,
    pagination_html: str = "",
) -> str:
    headers_text = "\n".join(f"{k}: {v}" for k, v in response.headers.items())
    try:
        response_json = response.json()
        response_text = json.dumps(response_json, ensure_ascii=False, indent=2)
        preview_html = build_table_preview(response_json)
    except ValueError:
        response_text = response.text
        preview_html = ""

    request_body = body if body else "(sin body)"
    return f"""
    <div class="box">
      <h2>Resultado</h2>
      <div class="box-body">
        <div class="result-title">{html.escape(method)} {html.escape(url)}</div>
        <p><strong>Status:</strong> {response.status_code}</p>
        {pagination_html}
        {preview_html}
        <p><strong>Request body:</strong></p>
        <pre>{html.escape(request_body)}</pre>
        <p><strong>Response headers:</strong></p>
        <pre>{html.escape(headers_text)}</pre>
        <p><strong>Response body:</strong></p>
        <pre>{html.escape(response_text)}</pre>
      </div>
    </div>
    """


def render_error(current_path: str, page_title: str, form_html: str, message: str) -> HTMLResponse:
    error_html = f'<div class="box"><h2>Error</h2><div class="box-body"><pre>{html.escape(message)}</pre></div></div>'
    return HTMLResponse(render_layout(current_path=current_path, page_title=page_title, form_html=form_html, result_html=error_html))


def perform_request(
    *,
    method: str,
    api_base_url: str,
    path: str,
    params: dict | None = None,
    json_body: dict | None = None,
    username: str | None = None,
    password: str | None = None,
) -> requests.Response:
    auth = (username, password) if username and password else None
    return requests.request(
        method=method,
        url=api_base_url.rstrip("/") + path,
        params={k: v for k, v in (params or {}).items() if v not in ("", None)},
        json=json_body,
        auth=auth,
        timeout=10,
    )


def form_health() -> str:
    return render_form_box(
        "GET /health",
        "/health",
        base_url_field() + '<div class="row"><input class="button" type="submit" value="Consultar health"></div>',
    )


def form_competitions() -> str:
    return render_form_box(
        "GET /competitions",
        "/competitions",
        base_url_field()
        + '<div class="row"><label>season</label><input name="season"></div>'
        + '<div class="row"><label>league</label><input name="league"></div>'
        + '<div class="row"><label>limit</label><input class="small" name="limit" value="20"></div>'
        + '<div class="row"><label>offset</label><input class="small" name="offset" value="0"></div>'
        + '<div class="row"><span class="hint">Los listados usan paginación con limit y offset.</span></div>'
        + '<div class="row"><input class="button" type="submit" value="Listar competitions"></div>',
    )


def form_competition_detail() -> str:
    return render_form_box(
        "GET /competitions/{season}/{league}",
        "/competition-detail",
        base_url_field()
        + '<div class="row"><label>season</label><input name="season" value="2024-25"></div>'
        + '<div class="row"><label>league</label><input name="league" value="en.1"></div>'
        + '<div class="row"><input class="button" type="submit" value="Ver competition"></div>',
    )


def form_matches() -> str:
    return render_form_box(
        "GET /competitions/{season}/{league}/matches",
        "/matches",
        base_url_field()
        + '<div class="row"><label>season</label><input name="season" value="2024-25"></div>'
        + '<div class="row"><label>league</label><input name="league" value="en.1"></div>'
        + '<div class="row"><label>team</label><input name="team"></div>'
        + '<div class="row"><label>round</label><input name="round_name"></div>'
        + '<div class="row"><label>date</label><input name="date"></div>'
        + '<div class="row"><label>limit</label><input class="small" name="limit" value="20"></div>'
        + '<div class="row"><label>offset</label><input class="small" name="offset" value="0"></div>'
        + '<div class="row"><input class="button" type="submit" value="Listar matches"></div>',
    )


def form_match_detail() -> str:
    return render_form_box(
        "GET /competitions/{season}/{league}/matches/{match_id}",
        "/match-detail",
        base_url_field()
        + '<div class="row"><label>season</label><input name="season" value="2024-25"></div>'
        + '<div class="row"><label>league</label><input name="league" value="en.1"></div>'
        + '<div class="row"><label>match_id</label><input class="small" name="match_id" value="0"></div>'
        + '<div class="row"><input class="button" type="submit" value="Ver match"></div>',
    )


def form_match_create() -> str:
    return render_form_box(
        "POST /competitions/{season}/{league}/matches",
        "/match-create",
        base_url_field()
        + '<div class="row"><label>Usuario Basic Auth</label><input name="username" value="admin"></div>'
        + '<div class="row"><label>Password Basic Auth</label><input name="password" value="admin123" type="password"></div>'
        + '<div class="row"><label>season</label><input name="season" value="2025"></div>'
        + '<div class="row"><label>league</label><input name="league" value="mls"></div>'
        + '<div class="row"><label>round</label><input name="round" value="Matchday X"></div>'
        + '<div class="row"><label>date</label><input name="date" value="2099-01-01"></div>'
        + '<div class="row"><label>time</label><input name="time" value="20:00"></div>'
        + '<div class="row"><label>team1</label><input name="team1" value="Equipo A"></div>'
        + '<div class="row"><label>team2</label><input name="team2" value="Equipo B"></div>'
        + '<div class="row"><label>HT score</label><input class="small" name="ht_home" value="0"> <input class="small" name="ht_away" value="0"></div>'
        + '<div class="row"><label>FT score</label><input class="small" name="ft_home" value="1"> <input class="small" name="ft_away" value="0"></div>'
        + '<div class="row"><input class="button" type="submit" value="Crear match"></div>',
    )


def form_match_delete() -> str:
    return render_form_box(
        "DELETE /competitions/{season}/{league}/matches/{match_id}",
        "/match-delete",
        base_url_field()
        + '<div class="row"><label>Usuario Basic Auth</label><input name="username" value="admin"></div>'
        + '<div class="row"><label>Password Basic Auth</label><input name="password" value="admin123" type="password"></div>'
        + '<div class="row"><label>season</label><input name="season" value="2025"></div>'
        + '<div class="row"><label>league</label><input name="league" value="mls"></div>'
        + '<div class="row"><label>match_id</label><input class="small" name="match_id" value="0"></div>'
        + '<div class="row"><input class="button" type="submit" value="Borrar match"></div>',
    )


def form_rate_limit_get() -> str:
    return render_form_box(
        "GET /rate-limit",
        "/rate-limit",
        base_url_field()
        + '<div class="row"><label>Usuario Basic Auth</label><input name="username" value="admin"></div>'
        + '<div class="row"><label>Password Basic Auth</label><input name="password" value="admin123" type="password"></div>'
        + '<div class="row"><input class="button" type="submit" value="Ver rate limit"></div>',
    )


def form_rate_limit_update() -> str:
    return render_form_box(
        "PUT /rate-limit",
        "/rate-limit-update",
        base_url_field()
        + '<div class="row"><label>Usuario Basic Auth</label><input name="username" value="admin"></div>'
        + '<div class="row"><label>Password Basic Auth</label><input name="password" value="admin123" type="password"></div>'
        + '<div class="row"><label>requests</label><input class="small" name="requests_limit" value="5"></div>'
        + '<div class="row"><label>window_seconds</label><input class="small" name="window_seconds" value="1"></div>'
        + '<div class="row"><input class="button" type="submit" value="Actualizar rate limit"></div>',
    )


@app.get("/", response_class=HTMLResponse)
def home():
    return RedirectResponse(url="/health", status_code=302)


@app.get("/health", response_class=HTMLResponse)
def health_page():
    return HTMLResponse(render_layout(current_path="/health", page_title="Health", form_html=form_health()))


@app.post("/health", response_class=HTMLResponse)
def health_action(api_base_url: str = Form(...)):
    form_html = form_health()
    try:
        response = perform_request(method="GET", api_base_url=api_base_url, path="/health")
    except requests.RequestException as exc:
        return render_error("/health", "Health", form_html, str(exc))
    result = build_result_html(method="GET", url=f"{api_base_url.rstrip('/')}/health", response=response)
    return HTMLResponse(render_layout(current_path="/health", page_title="Health", form_html=form_html, result_html=result))


@app.get("/competitions", response_class=HTMLResponse)
def competitions_page():
    return HTMLResponse(render_layout(current_path="/competitions", page_title="Competitions", form_html=form_competitions()))


@app.post("/competitions", response_class=HTMLResponse)
def competitions_action(
    api_base_url: str = Form(...),
    season: str = Form(""),
    league: str = Form(""),
    limit: int = Form(20),
    offset: int = Form(0),
):
    form_html = form_competitions()
    params = {"season": season, "league": league, "limit": limit, "offset": offset}
    try:
        response = perform_request(method="GET", api_base_url=api_base_url, path="/competitions", params=params)
    except requests.RequestException as exc:
        return render_error("/competitions", "Competitions", form_html, str(exc))
    total_count = int(response.headers.get("X-Total-Count", "0"))
    pagination_html = build_pagination_html(
        action="/competitions",
        total_count=total_count,
        limit=limit,
        offset=offset,
        hidden_fields={"api_base_url": api_base_url, "season": season, "league": league, "limit": limit},
    )
    result = build_result_html(
        method="GET",
        url=f"{api_base_url.rstrip('/')}/competitions",
        response=response,
        pagination_html=pagination_html,
    )
    return HTMLResponse(render_layout(current_path="/competitions", page_title="Competitions", form_html=form_html, result_html=result))


@app.get("/competition-detail", response_class=HTMLResponse)
def competition_detail_page():
    return HTMLResponse(render_layout(current_path="/competition-detail", page_title="Competition detail", form_html=form_competition_detail()))


@app.post("/competition-detail", response_class=HTMLResponse)
def competition_detail_action(
    api_base_url: str = Form(...),
    season: str = Form(...),
    league: str = Form(...),
):
    form_html = form_competition_detail()
    path = f"/competitions/{season}/{league}"
    try:
        response = perform_request(method="GET", api_base_url=api_base_url, path=path)
    except requests.RequestException as exc:
        return render_error("/competition-detail", "Competition detail", form_html, str(exc))
    result = build_result_html(method="GET", url=f"{api_base_url.rstrip('/')}{path}", response=response)
    return HTMLResponse(render_layout(current_path="/competition-detail", page_title="Competition detail", form_html=form_html, result_html=result))


@app.get("/matches", response_class=HTMLResponse)
def matches_page():
    return HTMLResponse(render_layout(current_path="/matches", page_title="Matches", form_html=form_matches()))


@app.post("/matches", response_class=HTMLResponse)
def matches_action(
    api_base_url: str = Form(...),
    season: str = Form(...),
    league: str = Form(...),
    team: str = Form(""),
    round_name: str = Form(""),
    date: str = Form(""),
    limit: int = Form(20),
    offset: int = Form(0),
):
    form_html = form_matches()
    path = f"/competitions/{season}/{league}/matches"
    params = {"team": team, "round": round_name, "date": date, "limit": limit, "offset": offset}
    try:
        response = perform_request(method="GET", api_base_url=api_base_url, path=path, params=params)
    except requests.RequestException as exc:
        return render_error("/matches", "Matches", form_html, str(exc))
    total_count = int(response.headers.get("X-Total-Count", "0"))
    pagination_html = build_pagination_html(
        action="/matches",
        total_count=total_count,
        limit=limit,
        offset=offset,
        hidden_fields={
            "api_base_url": api_base_url,
            "season": season,
            "league": league,
            "team": team,
            "round_name": round_name,
            "date": date,
            "limit": limit,
        },
    )
    result = build_result_html(
        method="GET",
        url=f"{api_base_url.rstrip('/')}{path}",
        response=response,
        pagination_html=pagination_html,
    )
    return HTMLResponse(render_layout(current_path="/matches", page_title="Matches", form_html=form_html, result_html=result))


@app.get("/match-detail", response_class=HTMLResponse)
def match_detail_page():
    return HTMLResponse(render_layout(current_path="/match-detail", page_title="Match detail", form_html=form_match_detail()))


@app.post("/match-detail", response_class=HTMLResponse)
def match_detail_action(
    api_base_url: str = Form(...),
    season: str = Form(...),
    league: str = Form(...),
    match_id: int = Form(...),
):
    form_html = form_match_detail()
    path = f"/competitions/{season}/{league}/matches/{match_id}"
    try:
        response = perform_request(method="GET", api_base_url=api_base_url, path=path)
    except requests.RequestException as exc:
        return render_error("/match-detail", "Match detail", form_html, str(exc))
    result = build_result_html(method="GET", url=f"{api_base_url.rstrip('/')}{path}", response=response)
    return HTMLResponse(render_layout(current_path="/match-detail", page_title="Match detail", form_html=form_html, result_html=result))


@app.get("/match-create", response_class=HTMLResponse)
def match_create_page():
    return HTMLResponse(render_layout(current_path="/match-create", page_title="Crear match", form_html=form_match_create()))


@app.post("/match-create", response_class=HTMLResponse)
def match_create_action(
    api_base_url: str = Form(...),
    username: str = Form(""),
    password: str = Form(""),
    season: str = Form(...),
    league: str = Form(...),
    round: str = Form(...),
    date: str = Form(...),
    time_value: str = Form(..., alias="time"),
    team1: str = Form(...),
    team2: str = Form(...),
    ht_home: int = Form(...),
    ht_away: int = Form(...),
    ft_home: int = Form(...),
    ft_away: int = Form(...),
):
    form_html = form_match_create()
    path = f"/competitions/{season}/{league}/matches"
    payload = {
        "round": round,
        "date": date,
        "time": time_value,
        "team1": team1,
        "team2": team2,
        "score": {"ht": [ht_home, ht_away], "ft": [ft_home, ft_away]},
    }
    try:
        response = perform_request(method="POST", api_base_url=api_base_url, path=path, json_body=payload, username=username, password=password)
    except requests.RequestException as exc:
        return render_error("/match-create", "Crear match", form_html, str(exc))
    result = build_result_html(method="POST", url=f"{api_base_url.rstrip('/')}{path}", response=response, body=json.dumps(payload, ensure_ascii=False, indent=2))
    return HTMLResponse(render_layout(current_path="/match-create", page_title="Crear match", form_html=form_html, result_html=result))


@app.get("/match-delete", response_class=HTMLResponse)
def match_delete_page():
    return HTMLResponse(render_layout(current_path="/match-delete", page_title="Borrar match", form_html=form_match_delete()))


@app.post("/match-delete", response_class=HTMLResponse)
def match_delete_action(
    api_base_url: str = Form(...),
    username: str = Form(""),
    password: str = Form(""),
    season: str = Form(...),
    league: str = Form(...),
    match_id: int = Form(...),
):
    form_html = form_match_delete()
    path = f"/competitions/{season}/{league}/matches/{match_id}"
    try:
        response = perform_request(method="DELETE", api_base_url=api_base_url, path=path, username=username, password=password)
    except requests.RequestException as exc:
        return render_error("/match-delete", "Borrar match", form_html, str(exc))
    result = build_result_html(method="DELETE", url=f"{api_base_url.rstrip('/')}{path}", response=response)
    return HTMLResponse(render_layout(current_path="/match-delete", page_title="Borrar match", form_html=form_html, result_html=result))


@app.get("/rate-limit", response_class=HTMLResponse)
def rate_limit_page():
    return HTMLResponse(render_layout(current_path="/rate-limit", page_title="Ver rate limit", form_html=form_rate_limit_get()))


@app.post("/rate-limit", response_class=HTMLResponse)
def rate_limit_action(
    api_base_url: str = Form(...),
    username: str = Form(""),
    password: str = Form(""),
):
    form_html = form_rate_limit_get()
    path = "/rate-limit"
    try:
        response = perform_request(method="GET", api_base_url=api_base_url, path=path, username=username, password=password)
    except requests.RequestException as exc:
        return render_error("/rate-limit", "Ver rate limit", form_html, str(exc))
    result = build_result_html(method="GET", url=f"{api_base_url.rstrip('/')}{path}", response=response)
    return HTMLResponse(render_layout(current_path="/rate-limit", page_title="Ver rate limit", form_html=form_html, result_html=result))


@app.get("/rate-limit-update", response_class=HTMLResponse)
def rate_limit_update_page():
    return HTMLResponse(render_layout(current_path="/rate-limit-update", page_title="Actualizar rate limit", form_html=form_rate_limit_update()))


@app.post("/rate-limit-update", response_class=HTMLResponse)
def rate_limit_update_action(
    api_base_url: str = Form(...),
    username: str = Form(""),
    password: str = Form(""),
    requests_limit: int = Form(...),
    window_seconds: float = Form(...),
):
    form_html = form_rate_limit_update()
    path = "/rate-limit"
    payload = {"requests": requests_limit, "window_seconds": window_seconds}
    try:
        response = perform_request(method="PUT", api_base_url=api_base_url, path=path, json_body=payload, username=username, password=password)
    except requests.RequestException as exc:
        return render_error("/rate-limit-update", "Actualizar rate limit", form_html, str(exc))
    result = build_result_html(method="PUT", url=f"{api_base_url.rstrip('/')}{path}", response=response, body=json.dumps(payload, ensure_ascii=False, indent=2))
    return HTMLResponse(render_layout(current_path="/rate-limit-update", page_title="Actualizar rate limit", form_html=form_html, result_html=result))


if __name__ == "__main__":
    uvicorn.run("client.main:app", host="0.0.0.0", port=8001, reload=True)
