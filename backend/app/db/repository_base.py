from __future__ import annotations

from typing import Any, Generic, Protocol, TypeVar, runtime_checkable

T = TypeVar("T")


@runtime_checkable
class Repository(Protocol[T]):
    """DB-agnostic repository. Each adapter implements this for its backend."""

    async def get(self, id: str) -> T | None: ...

    async def list(
        self,
        filters: dict[str, Any] | None = None,
        page: int = 1,
        size: int = 20,
        order_by: str | None = None,
    ) -> tuple[list[T], int]: ...

    async def create(self, entity: T) -> T: ...

    async def update(self, id: str, data: dict[str, Any]) -> T: ...

    async def delete(self, id: str) -> bool: ...

    async def query(self, raw_query: Any, **kwargs) -> list[T]: ...


class BaseRepository(Generic[T]):
    """Convenience base class with shared serialization helpers."""

    model_cls: type[T]

    def _to_dict(self, entity: T) -> dict[str, Any]:
        import dataclasses
        return dataclasses.asdict(entity)  # type: ignore[arg-type]

    def _from_dict(self, data: dict[str, Any]) -> T:
        import dataclasses
        if dataclasses.is_dataclass(self.model_cls):
            fields = {f.name for f in dataclasses.fields(self.model_cls)}  # type: ignore
            filtered = {k: v for k, v in data.items() if k in fields}
            return self.model_cls(**filtered)  # type: ignore
        raise NotImplementedError("Override _from_dict for non-dataclass models")
