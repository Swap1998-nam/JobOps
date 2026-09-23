import os
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Literal

import psycopg
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from prometheus_client import Counter, generate_latest, CONTENT_TYPE_LATEST
from pydantic import BaseModel, Field
from starlette.responses import Response

DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://jobops:jobops@localhost:5432/jobops')
CREATED = Counter('jobops_applications_created_total', 'Applications created')


def connection():
    return psycopg.connect(DATABASE_URL)


@asynccontextmanager
async def lifespan(app: FastAPI):
    with connection() as db:
        db.execute('CREATE TABLE IF NOT EXISTS applications (id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY, company TEXT NOT NULL, role TEXT NOT NULL, status TEXT NOT NULL, created_at TIMESTAMPTZ NOT NULL)')
        db.commit()
    yield


app = FastAPI(title='JobOps', lifespan=lifespan)


class Application(BaseModel):
    company: str = Field(min_length=1, max_length=120)
    role: str = Field(min_length=1, max_length=120)
    status: Literal['saved', 'applied', 'interview', 'offer', 'rejected'] = 'saved'


@app.get('/health/live')
def live():
    return {'status': 'ok'}


@app.get('/health/ready')
def ready():
    try:
        with connection() as db:
            db.execute('SELECT 1')
        return {'status': 'ready'}
    except psycopg.Error:
        raise HTTPException(503, 'database unavailable')


@app.get('/metrics')
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.get('/api/applications')
def list_applications():
    with connection() as db:
        rows = db.execute('SELECT id, company, role, status, created_at FROM applications ORDER BY id DESC').fetchall()
    return [dict(zip(('id', 'company', 'role', 'status', 'created_at'), row)) for row in rows]


@app.post('/api/applications', status_code=201)
def create_application(item: Application):
    with connection() as db:
        row = db.execute('INSERT INTO applications (company, role, status, created_at) VALUES (%s, %s, %s, %s) RETURNING id', (item.company, item.role, item.status, datetime.now(timezone.utc))).fetchone()
        db.commit()
    CREATED.inc()
    return {'id': row[0], **item.model_dump()}


@app.patch('/api/applications/{item_id}')
def update_application(item_id: int, status: Literal['saved', 'applied', 'interview', 'offer', 'rejected']):
    with connection() as db:
        row = db.execute('UPDATE applications SET status = %s WHERE id = %s RETURNING id', (status, item_id)).fetchone()
        db.commit()
    if row is None:
        raise HTTPException(404, 'application not found')
    return {'id': item_id, 'status': status}


@app.get('/', response_class=HTMLResponse)
def home():
    return '''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>JobOps</title><style>body{font:16px system-ui;max-width:760px;margin:3rem auto;padding:0 1rem;color:#182235}input,button,select{padding:.7rem;margin:.2rem}li{padding:.6rem;border-bottom:1px solid #ddd}small{color:#586477}</style><h1>JobOps</h1><p>Track your cloud and DevOps applications.</p><form id="form"><input name="company" placeholder="Company" required maxlength="120"><input name="role" placeholder="Role" required maxlength="120"><button>Add application</button></form><p id="message" role="status"></p><ul id="list"></ul><script>const states=['saved','applied','interview','offer','rejected'];async function load(){try{const r=await fetch('/api/applications');if(!r.ok)throw Error('Could not load applications');const items=await r.json();const list=document.querySelector('#list');list.replaceChildren();for(const item of items){const li=document.createElement('li');const title=document.createElement('strong');title.textContent=item.company+' — '+item.role+' ';const select=document.createElement('select');select.setAttribute('aria-label','Status for '+item.company);for(const state of states){const o=document.createElement('option');o.value=state;o.textContent=state;select.append(o)}select.value=item.status;select.onchange=async()=>{const result=await fetch('/api/applications/'+item.id+'?status='+encodeURIComponent(select.value),{method:'PATCH'});if(!result.ok){document.querySelector('#message').textContent='Update failed';await load()}};li.append(title,select);list.append(li)}}catch(e){document.querySelector('#message').textContent=e.message}}document.querySelector('#form').onsubmit=async e=>{e.preventDefault();const form=e.target;const body=Object.fromEntries(new FormData(form));const r=await fetch('/api/applications',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});document.querySelector('#message').textContent=r.ok?'Application added':'Could not add application';if(r.ok){form.reset();await load()}};load()</script></html>'''
