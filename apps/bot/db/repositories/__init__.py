"""Repositories (data access objects) for ORM models."""

from .bots import BotsRepository
from .documents import DocumentsRepository

__all__ = ["BotsRepository", "DocumentsRepository"]
