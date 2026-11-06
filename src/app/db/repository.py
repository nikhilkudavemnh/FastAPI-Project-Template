"""Generic async CRUD repository. Subclass per model (or use directly) and add domain
queries. Services should talk to repositories, routers should talk to services."""

import uuid
from collections.abc import Sequence
from typing import Any

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.pagination import Page, PageParams
from app.db.base import Base


class Repository[M: Base]:
    model: type[M]

    def __init__(self, session: AsyncSession, model: type[M] | None = None) -> None:
        self.session = session
        if model is not None:
            self.model = model

    # ---- reads ----
    def query(self) -> Select[M]:
        return select(self.model)

    async def get(self, id_: uuid.UUID) -> M | None:
        return await self.session.get(self.model, id_)

    async def get_by(self, **filters: Any) -> M | None:
        res = await self.session.scalars(self.query().filter_by(**filters).limit(1))
        return res.one_or_none()

    async def list(
        self, params: PageParams, stmt: Select[M] | None = None, **filters: Any
    ) -> Page[M]:
        stmt = (stmt if stmt is not None else self.query()).filter_by(**filters)
        total = await self.session.scalar(select(func.count()).select_from(stmt.subquery()))
        rows = await self.session.scalars(stmt.offset(params.offset).limit(params.size))
        return Page(items=list(rows.all()), total=total or 0, page=params.page, size=params.size)

    async def all(self, **filters: Any) -> Sequence[M]:
        res = await self.session.scalars(self.query().filter_by(**filters))
        return res.all()

    async def exists(self, **filters: Any) -> bool:
        res = await self.session.execute(select(self.query().filter_by(**filters).exists()))
        return bool(res.scalar())

    # ---- writes (flush, don't commit: the request session commits once) ----
    async def create(self, **data: Any) -> M:
        obj = self.model(**data)
        self.session.add(obj)
        await self.session.flush()
        await self.session.refresh(obj)
        return obj

    async def update(self, obj: M, **data: Any) -> M:
        for key, value in data.items():
            setattr(obj, key, value)
        await self.session.flush()
        await self.session.refresh(obj)
        return obj

    async def delete(self, obj: M) -> None:
        await self.session.delete(obj)
        await self.session.flush()
