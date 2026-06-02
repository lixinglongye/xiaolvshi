import logging
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

ModelT = TypeVar("ModelT")

logger = logging.getLogger(__name__)


class BaseCrudService(Generic[ModelT]):
    """Shared async CRUD implementation for generated entity services."""

    model: Type[ModelT]
    entity_name: str = "entity"
    owner_field: str = "user_id"

    def __init__(self, db: AsyncSession):
        self.db = db

    @property
    def _id_column(self):
        return getattr(self.model, "id")

    @property
    def _owner_column(self):
        return getattr(self.model, self.owner_field, None)

    def _apply_owner(self, query, user_id: Optional[str]):
        owner_column = self._owner_column
        if user_id and owner_column is not None:
            return query.where(owner_column == user_id)
        return query

    async def create(self, data: Dict[str, Any], user_id: Optional[str] = None) -> Optional[ModelT]:
        payload = dict(data)
        if user_id and self._owner_column is not None:
            payload[self.owner_field] = user_id
        try:
            obj = self.model(**payload)
            self.db.add(obj)
            await self.db.commit()
            await self.db.refresh(obj)
            logger.info("Created %s with id: %s", self.entity_name, getattr(obj, "id", None))
            return obj
        except Exception:
            await self.db.rollback()
            logger.exception("Error creating %s", self.entity_name)
            raise

    async def check_ownership(self, obj_id: int, user_id: str) -> bool:
        try:
            return await self.get_by_id(obj_id, user_id=user_id) is not None
        except Exception:
            logger.exception("Error checking ownership for %s %s", self.entity_name, obj_id)
            return False

    async def get_by_id(self, obj_id: int, user_id: Optional[str] = None) -> Optional[ModelT]:
        try:
            query = select(self.model).where(self._id_column == obj_id)
            query = self._apply_owner(query, user_id)
            result = await self.db.execute(query)
            return result.scalar_one_or_none()
        except Exception:
            logger.exception("Error fetching %s %s", self.entity_name, obj_id)
            raise

    async def get_list(
        self,
        skip: int = 0,
        limit: int = 20,
        user_id: Optional[str] = None,
        query_dict: Optional[Dict[str, Any]] = None,
        sort: Optional[str] = None,
    ) -> Dict[str, Any]:
        try:
            query = select(self.model)
            count_query = select(func.count(self._id_column))
            query = self._apply_owner(query, user_id)
            count_query = self._apply_owner(count_query, user_id)

            if query_dict:
                for field, value in query_dict.items():
                    if hasattr(self.model, field):
                        column = getattr(self.model, field)
                        query = query.where(column == value)
                        count_query = count_query.where(column == value)

            count_result = await self.db.execute(count_query)
            total = count_result.scalar() or 0

            if sort:
                descending = sort.startswith("-")
                field_name = sort[1:] if descending else sort
                if hasattr(self.model, field_name):
                    column = getattr(self.model, field_name)
                    query = query.order_by(column.desc() if descending else column)
            else:
                query = query.order_by(self._id_column.desc())

            result = await self.db.execute(query.offset(skip).limit(limit))
            return {
                "items": result.scalars().all(),
                "total": total,
                "skip": skip,
                "limit": limit,
            }
        except Exception:
            logger.exception("Error fetching %s list", self.entity_name)
            raise

    async def update(
        self,
        obj_id: int,
        update_data: Dict[str, Any],
        user_id: Optional[str] = None,
    ) -> Optional[ModelT]:
        try:
            obj = await self.get_by_id(obj_id, user_id=user_id)
            if not obj:
                logger.warning("%s %s not found for update", self.entity_name, obj_id)
                return None
            for key, value in update_data.items():
                if hasattr(obj, key) and key != self.owner_field:
                    setattr(obj, key, value)
            await self.db.commit()
            await self.db.refresh(obj)
            logger.info("Updated %s %s", self.entity_name, obj_id)
            return obj
        except Exception:
            await self.db.rollback()
            logger.exception("Error updating %s %s", self.entity_name, obj_id)
            raise

    async def delete(self, obj_id: int, user_id: Optional[str] = None) -> bool:
        try:
            obj = await self.get_by_id(obj_id, user_id=user_id)
            if not obj:
                logger.warning("%s %s not found for deletion", self.entity_name, obj_id)
                return False
            await self.db.delete(obj)
            await self.db.commit()
            logger.info("Deleted %s %s", self.entity_name, obj_id)
            return True
        except Exception:
            await self.db.rollback()
            logger.exception("Error deleting %s %s", self.entity_name, obj_id)
            raise

    async def get_by_field(
        self,
        field_name: str,
        field_value: Any,
        user_id: Optional[str] = None,
    ) -> Optional[ModelT]:
        try:
            if not hasattr(self.model, field_name):
                raise ValueError(f"Field {field_name} does not exist on {self.model.__name__}")
            query = select(self.model).where(getattr(self.model, field_name) == field_value)
            query = self._apply_owner(query, user_id)
            result = await self.db.execute(query)
            return result.scalar_one_or_none()
        except Exception:
            logger.exception("Error fetching %s by %s", self.entity_name, field_name)
            raise

    async def list_by_field(
        self,
        field_name: str,
        field_value: Any,
        skip: int = 0,
        limit: int = 20,
        user_id: Optional[str] = None,
    ) -> List[ModelT]:
        try:
            if not hasattr(self.model, field_name):
                raise ValueError(f"Field {field_name} does not exist on {self.model.__name__}")
            query = (
                select(self.model)
                .where(getattr(self.model, field_name) == field_value)
                .order_by(self._id_column.desc())
                .offset(skip)
                .limit(limit)
            )
            query = self._apply_owner(query, user_id)
            result = await self.db.execute(query)
            return result.scalars().all()
        except Exception:
            logger.exception("Error fetching %s by %s", self.entity_name, field_name)
            raise
