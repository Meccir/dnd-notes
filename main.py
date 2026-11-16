from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from db import get_conn

app = FastAPI()
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")


# Главная: список энкаунтеров
@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    with get_conn() as conn:
        rows = conn.execute(
            "select id, name, round from encounters order by created_at desc"
        ).fetchall()
    return templates.TemplateResponse(request, "index.html", {
        "encounters": rows,
    })


# Создание энкаунтера
@app.post("/encounters")
def create_encounter(name: str = Form(...)):
    with get_conn() as conn:
        conn.execute("insert into encounters (name) values (%s)", (name,))
        conn.commit()
    return RedirectResponse("/", status_code=303)


# Удаление энкаунтера
@app.post("/encounters/{enc_id}/delete")
def delete_encounter(enc_id: str):
    with get_conn() as conn:
        conn.execute("delete from encounters where id = %s", (enc_id,))
        conn.commit()
    return RedirectResponse("/", status_code=303)


# Страница конкретного боя
@app.get("/encounters/{enc_id}", response_class=HTMLResponse)
def encounter_page(request: Request, enc_id: str):
    with get_conn() as conn:
        enc = conn.execute(
            "select id, name, round, turn_index from encounters where id = %s",
            (enc_id,),
        ).fetchone()
        combatants = conn.execute(
            "select id, name, initiative, hp, max_hp, side from combatants "
            "where encounter_id = %s order by initiative desc",
            (enc_id,),
        ).fetchall()
    return templates.TemplateResponse(request, "encounter.html", {
        "enc": enc,
        "combatants": combatants,
    })


# Добавление участника боя
@app.post("/encounters/{enc_id}/combatants")
def add_combatant(enc_id: str, name: str = Form(...),
                  initiative: int = Form(...), hp: int = Form(...),
                  side: str = Form(...)):
    with get_conn() as conn:
        conn.execute(
            "insert into combatants (encounter_id, name, initiative, hp, max_hp, side) "
            "values (%s, %s, %s, %s, %s, %s)",
            (enc_id, name, initiative, hp, hp, side),
        )
        conn.commit()
    return RedirectResponse(f"/encounters/{enc_id}", status_code=303)