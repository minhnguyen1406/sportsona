"""Natural-language → SQL stats engine.

Public entry point: ``app.features.ask.service.answer_question``. Kept
import-free so the model registry can load ``ask`` models without dragging
in the LLM service layer (which imports the registry back).
"""
