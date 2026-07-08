"""Daily-cached AI-generated F1 stat. Public entry point: ``get_or_generate``."""

from app.services.stat_of_day.service import StatOfDayFailure, get_or_generate

__all__ = ["StatOfDayFailure", "get_or_generate"]
