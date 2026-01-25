# StudioPilates

## Setup local

1) Crie `.env` com base em `.env.example`.
2) Instale dependencias:

```
pip install -r requirements.txt
```

3) Rode migrations:

```
python backend/manage.py migrate
```

4) Crie superuser:

```
python backend/manage.py createsuperuser
```

5) Suba Django e FastAPI:

```
python backend/manage.py runserver
uvicorn api.main:app --reload
```

## API

- Token: `POST /api/auth/token` com `username` e `password`.
- Swagger: `/docs` no FastAPI.

## VM / Postgres

Use `docker-compose.yml` e configure `DATABASE_URL` no `.env`.
