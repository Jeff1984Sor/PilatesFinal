from sqlalchemy import MetaData, create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import settings

NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

metadata = MetaData(naming_convention=NAMING_CONVENTION)


class Base(DeclarativeBase):
    metadata = metadata


def get_engine():
    connect_args = {}
    if settings.DATABASE_URL.startswith("sqlite"):
        connect_args = {"check_same_thread": False}
    return create_engine(settings.DATABASE_URL, future=True, connect_args=connect_args)


engine = get_engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def import_all_models() -> None:
    from app.modules.auth import models as _auth  # noqa: F401
    from app.modules.profissionais import models as _prof  # noqa: F401
    from app.modules.unidades import models as _unidades  # noqa: F401
    from app.modules.termos import models as _termos  # noqa: F401
    from app.modules.alunos import models as _alunos  # noqa: F401
    from app.modules.planos import models as _planos  # noqa: F401
    from app.modules.contratos import models as _contratos  # noqa: F401
    from app.modules.financeiro import models as _financeiro  # noqa: F401
    from app.modules.agenda import models as _agenda  # noqa: F401
    from app.modules.integracoes import models as _integracoes  # noqa: F401
