from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.middleware.base import BaseHTTPMiddleware
from starlette import status

from app.core.logging import configure_logging, new_request_id, request_id_ctx
from app.core.config import settings
from app.core.exceptions import validation_exception_handler, unhandled_exception_handler

from app.modules.auth.router import router as auth_router
from app.modules.profissionais.router import router as profissionais_router
from app.modules.alunos.router import router as alunos_router
from app.modules.unidades.router import router as unidades_router
from app.modules.planos.router import router as planos_router
from app.modules.contratos.router import router as contratos_router
from app.modules.termos.router import router as termos_router
from app.modules.financeiro.router import router as financeiro_router
from app.modules.agenda.router import router as agenda_router
from app.modules.integracoes.router import router as integracoes_router

configure_logging()

app = FastAPI(title="StudioPilates API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class RequestIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID") or new_request_id()
        token = request_id_ctx.set(request_id)
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        request_id_ctx.reset(token)
        return response


app.add_middleware(RequestIdMiddleware)

app.add_exception_handler(Exception, unhandled_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)

app.include_router(auth_router)
app.include_router(profissionais_router)
app.include_router(alunos_router)
app.include_router(unidades_router)
app.include_router(planos_router)
app.include_router(contratos_router)
app.include_router(termos_router)
app.include_router(financeiro_router)
app.include_router(agenda_router)
app.include_router(integracoes_router)


@app.get("/health", tags=["health"])
def health():
    return {"status": "ok"}
