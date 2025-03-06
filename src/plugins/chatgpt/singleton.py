from typing import Any, ClassVar, Self


class _Singleton(type):
    _instance: ClassVar[Any | None] = None

    def __call__(cls: type[Self], *args, **kwargs) -> Self:
        if cls._instance is None:
            cls._instance = super(_Singleton, cls).__call__(*args, **kwargs)
        return cls._instance


class Singleton(metaclass=_Singleton):
    pass
