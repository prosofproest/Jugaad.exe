"""Conversational capture module.

A conversation is a private thread owned by one user. It wraps the photo
assessment pipeline; it never computes a prediction. Conversations, messages,
uploads and review requests are persisted through SQLAlchemy (Alembic
``0002_chat_persistence``); replies come from the pluggable assessment engine
and are content-validated before storage. No real image model is connected yet,
so the default engine is a visibly labelled demo.
"""
