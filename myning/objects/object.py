from abc import abstractmethod
from typing import Type, TypeVar

T = TypeVar("T", bound="Object")


class Object:
    file_name: str

    @abstractmethod
    def to_dict(self) -> dict:
        pass

    @classmethod
    @abstractmethod
    def from_dict(cls: Type[T], d: dict) -> T:
        pass
