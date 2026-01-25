from typing import Any, Generic, TypeVar
from sqlalchemy import select, func

ModelType = TypeVar("ModelType")


class BaseRepository(Generic[ModelType]):
    def __init__(self, db, model: type[ModelType]):
        self.db = db
        self.model = model

    def get(self, id: int) -> ModelType | None:
        return self.db.get(self.model, id)

    def list(self, filters=None, order_by: str | None = None, order_dir: str = "asc", offset: int = 0, limit: int = 20):
        filters = filters or []
        stmt = select(self.model)
        for f in filters:
            stmt = stmt.where(f)
        if order_by and hasattr(self.model, order_by):
            col = getattr(self.model, order_by)
            stmt = stmt.order_by(col.desc() if order_dir == "desc" else col.asc())
        total = self.db.execute(select(func.count()).select_from(stmt.subquery())).scalar_one()
        items = self.db.execute(stmt.offset(offset).limit(limit)).scalars().all()
        return items, total

    def create(self, obj_in: dict[str, Any]) -> ModelType:
        db_obj = self.model(**obj_in)
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def update(self, db_obj: ModelType, obj_in: dict[str, Any]) -> ModelType:
        for k, v in obj_in.items():
            setattr(db_obj, k, v)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def delete(self, db_obj: ModelType) -> None:
        self.db.delete(db_obj)
        self.db.commit()
