"""Forecast-driven alerts, deduplication, delivery and feedback.

No production delivery provider is bundled. A deployment that has not approved
a channel leaves deliveries recorded as failed instead of pretending they were
sent.
"""
