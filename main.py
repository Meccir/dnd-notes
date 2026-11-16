from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from db import get_conn

app = FastAPI()
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

CARD_TYPES = {
    "character": "Персонаж",
    "place": "Место",
    "description": "Общее описание",
}


@app.on_event("startup")
def create_lore_tables():
    with get_conn() as conn:
        conn.execute(
            "create table if not exists lore_campaigns ("
            "id uuid primary key default gen_random_uuid(), "
            "name text not null, created_at timestamptz not null default now())"
        )
        conn.execute(
            "create table if not exists lore_cards ("
            "id uuid primary key default gen_random_uuid(), "
            "campaign_id uuid not null references lore_campaigns(id) on delete cascade, "
            "kind text not null check (kind in ('character', 'place', 'description')), "
            "title text not null, content text not null default '', "
            "created_at timestamptz not null default now())"
        )
        conn.commit()


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


# --- Партии (кампании) ---

# Список партий
@app.get("/campaigns", response_class=HTMLResponse)
def campaigns_list(request: Request):
    with get_conn() as conn:
        rows = conn.execute(
            "select id, name, notes, created_at from campaigns order by created_at desc"
        ).fetchall()
    return templates.TemplateResponse(request, "campaigns.html", {
        "campaigns": rows,
    })


# Создание партии
@app.post("/campaigns")
def create_campaign(name: str = Form(...)):
    with get_conn() as conn:
        conn.execute("insert into campaigns (name) values (%s)", (name,))
        conn.commit()
    return RedirectResponse("/campaigns", status_code=303)


# Страница партии с заметками
@app.get("/campaigns/{camp_id}", response_class=HTMLResponse)
def campaign_page(request: Request, camp_id: str):
    with get_conn() as conn:
        camp = conn.execute(
            "select id, name, notes from campaigns where id = %s", (camp_id,)
        ).fetchone()
    if camp is None:
        raise HTTPException(status_code=404, detail="Партия не найдена")
    return templates.TemplateResponse(request, "campaign.html", {
        "camp": camp,
    })


# Сохранение названия и заметок
@app.post("/campaigns/{camp_id}/save")
def save_campaign(camp_id: str, name: str = Form(...), notes: str = Form("")):
    with get_conn() as conn:
        conn.execute(
            "update campaigns set name = %s, notes = %s where id = %s",
            (name, notes, camp_id),
        )
        conn.commit()
    return RedirectResponse(f"/campaigns/{camp_id}", status_code=303)


# Удаление партии
@app.post("/campaigns/{camp_id}/delete")
def delete_campaign(camp_id: str):
    with get_conn() as conn:
        conn.execute("delete from campaigns where id = %s", (camp_id,))
        conn.commit()
    return RedirectResponse("/campaigns", status_code=303)


# --- Лор ---

@app.get("/lore", response_class=HTMLResponse)
def lore_list(request: Request):
    with get_conn() as conn:
        rows = conn.execute(
            "select id, name from lore_campaigns order by created_at desc"
        ).fetchall()
    return templates.TemplateResponse(request, "lore.html", {"campaigns": rows})


@app.post("/lore")
def create_lore_campaign(name: str = Form(...)):
    name = name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="Укажи название кампании")
    with get_conn() as conn:
        conn.execute("insert into lore_campaigns (name) values (%s)", (name,))
        conn.commit()
    return RedirectResponse("/lore", status_code=303)


@app.post("/lore/{campaign_id}/delete")
def delete_lore_campaign(campaign_id: str):
    with get_conn() as conn:
        conn.execute("delete from lore_campaigns where id = %s", (campaign_id,))
        conn.commit()
    return RedirectResponse("/lore", status_code=303)


@app.get("/lore/{campaign_id}", response_class=HTMLResponse)
def lore_campaign_page(request: Request, campaign_id: str):
    with get_conn() as conn:
        campaign = conn.execute(
            "select id, name from lore_campaigns where id = %s", (campaign_id,)
        ).fetchone()
        if campaign is None:
            raise HTTPException(status_code=404, detail="Кампания лора не найдена")
        cards = conn.execute(
            "select id, kind, title, content from lore_cards "
            "where campaign_id = %s order by created_at",
            (campaign_id,),
        ).fetchall()
    return templates.TemplateResponse(request, "lore_campaign.html", {
        "campaign": campaign,
        "cards": cards,
        "card_types": list(CARD_TYPES.items()),
    })


@app.post("/lore/{campaign_id}/cards")
def create_lore_card(campaign_id: str, title: str = Form(...),
                     kind: str = Form(...), content: str = Form("")):
    title = title.strip()
    if not title:
        raise HTTPException(status_code=400, detail="Укажи название карточки")
    if kind not in CARD_TYPES:
        raise HTTPException(status_code=400, detail="Неизвестный тип карточки")
    with get_conn() as conn:
        campaign = conn.execute(
            "select id from lore_campaigns where id = %s", (campaign_id,)
        ).fetchone()
        if campaign is None:
            raise HTTPException(status_code=404, detail="Кампания лора не найдена")
        conn.execute(
            "insert into lore_cards (campaign_id, kind, title, content) "
            "values (%s, %s, %s, %s)", (campaign_id, kind, title, content)
        )
        conn.commit()
    return RedirectResponse(f"/lore/{campaign_id}", status_code=303)


@app.post("/lore/{campaign_id}/cards/{card_id}/save")
def save_lore_card(campaign_id: str, card_id: str,
                   title: str = Form(...), kind: str = Form(...),
                   content: str = Form("")):
    title = title.strip()
    if not title:
        raise HTTPException(status_code=400, detail="Укажи название карточки")
    if kind not in CARD_TYPES:
        raise HTTPException(status_code=400, detail="Неизвестный тип карточки")
    with get_conn() as conn:
        conn.execute(
            "update lore_cards set title = %s, kind = %s, content = %s "
            "where id = %s and campaign_id = %s",
            (title, kind, content, card_id, campaign_id),
        )
        conn.commit()
    return RedirectResponse(f"/lore/{campaign_id}", status_code=303)


@app.post("/lore/{campaign_id}/cards/{card_id}/delete")
def delete_lore_card(campaign_id: str, card_id: str):
    with get_conn() as conn:
        conn.execute(
            "delete from lore_cards where id = %s and campaign_id = %s",
            (card_id, campaign_id),
        )
        conn.commit()
    return RedirectResponse(f"/lore/{campaign_id}", status_code=303)
