"""Natural-language → SQL stats engine.

Public entry point is :func:`answer_question`. It generates a SELECT against
the ``f1`` schema via Claude, validates it, runs it in a read-only
transaction, and returns the rows plus the SQL that produced them.
"""

from app.services.ask.service import AskFailure, answer_question

__all__ = ["AskFailure", "answer_question"]
