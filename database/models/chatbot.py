"""
CropSentinel AI — Domain 10: Chatbot and Knowledge Database
Tables:
- chat_sessions
- chat_messages
- knowledge_articles
- knowledge_chunks
- knowledge_embeddings
- chatbot_feedback

COMPLIANCE:
Supports chat history, strict message ordering, knowledge article versioning,
knowledge chunking, vector embeddings with pgvector compatibility, and feedback.
"""

import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from database.models.base import (
    Base,
    PortableUUID,
    TimestampMixin,
    VectorType,
)


class ChatSession(Base, TimestampMixin):
    """Agricultural AI advisory chat session."""
    __tablename__ = "chat_sessions"

    id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID,
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(150), default="New Conversation", nullable=False)
    language: Mapped[str] = mapped_column(String(10), default="en", nullable=False)
    channel: Mapped[str] = mapped_column(String(20), default="mobile", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        CheckConstraint(
            "channel IN ('web', 'mobile', 'whatsapp', 'sms', 'ivr')",
            name="chk_chat_sessions_channel",
        ),
    )

    user: Mapped["User"] = relationship("User")
    messages: Mapped[List["ChatMessage"]] = relationship(
        "ChatMessage", back_populates="session", cascade="all, delete-orphan", order_by="ChatMessage.sequence_number"
    )


class ChatMessage(Base):
    """Ordered conversational dialogue messages."""
    __tablename__ = "chat_messages"

    id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID,
        primary_key=True,
        default=uuid.uuid4,
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID,
        ForeignKey("chat_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    sender_type: Mapped[str] = mapped_column(String(20), nullable=False)
    message_text: Mapped[str] = mapped_column(Text, nullable=False)
    sequence_number: Mapped[int] = mapped_column(Integer, nullable=False)
    cited_sources: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    sent_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint("session_id", "sequence_number", name="uq_chat_session_seq"),
        CheckConstraint(
            "sender_type IN ('user', 'bot', 'expert_agent', 'system')",
            name="chk_chat_messages_sender_type",
        ),
    )

    session: Mapped["ChatSession"] = relationship("ChatSession", back_populates="messages")
    feedbacks: Mapped[List["ChatbotFeedback"]] = relationship(
        "ChatbotFeedback", back_populates="message", cascade="all, delete-orphan"
    )


class KnowledgeArticle(Base, TimestampMixin):
    """Versioned agricultural extension and pathology knowledge base article."""
    __tablename__ = "knowledge_articles"

    id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID,
        primary_key=True,
        default=uuid.uuid4,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    author_id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID,
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    category: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="published", nullable=False)
    is_current: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        CheckConstraint(
            "status IN ('draft', 'under_review', 'published', 'archived')",
            name="chk_knowledge_art_status",
        ),
        CheckConstraint("version >= 1", name="chk_knowledge_art_version_pos"),
    )

    author: Mapped["User"] = relationship("User")
    chunks: Mapped[List["KnowledgeChunk"]] = relationship(
        "KnowledgeChunk", back_populates="article", cascade="all, delete-orphan"
    )


class KnowledgeChunk(Base):
    """Chunked passages from knowledge articles for RAG retrieval."""
    __tablename__ = "knowledge_chunks"

    id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID,
        primary_key=True,
        default=uuid.uuid4,
    )
    article_id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID,
        ForeignKey("knowledge_articles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    content_chunk: Mapped[str] = mapped_column(Text, nullable=False)
    token_count: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint("article_id", "chunk_index", name="uq_art_chunk_index"),
        CheckConstraint("chunk_index >= 0", name="chk_chunk_idx_nonneg"),
        CheckConstraint("token_count > 0", name="chk_chunk_token_pos"),
    )

    article: Mapped["KnowledgeArticle"] = relationship("KnowledgeArticle", back_populates="chunks")
    embeddings: Mapped[List["KnowledgeEmbedding"]] = relationship(
        "KnowledgeEmbedding", back_populates="chunk", cascade="all, delete-orphan"
    )


class KnowledgeEmbedding(Base):
    """Dense vector representations stored for semantic search (compatible with pgvector)."""
    __tablename__ = "knowledge_embeddings"

    id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID,
        primary_key=True,
        default=uuid.uuid4,
    )
    chunk_id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID,
        ForeignKey("knowledge_chunks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    embedding_model: Mapped[str] = mapped_column(String(100), nullable=False)
    embedding_vector: Mapped[str] = mapped_column(
        VectorType(1536),
        nullable=False,
    )
    dimension: Mapped[int] = mapped_column(Integer, default=1536, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    __table_args__ = (
        CheckConstraint("dimension > 0", name="chk_embed_dim_positive"),
    )

    chunk: Mapped["KnowledgeChunk"] = relationship("KnowledgeChunk", back_populates="embeddings")


class ChatbotFeedback(Base):
    """Farmer and user qualitative feedback on conversational responses."""
    __tablename__ = "chatbot_feedback"

    id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID,
        primary_key=True,
        default=uuid.uuid4,
    )
    message_id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID,
        ForeignKey("chat_messages.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID,
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    rating: Mapped[int] = mapped_column(Integer, nullable=False)
    is_helpful: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    feedback_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    submitted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    __table_args__ = (
        CheckConstraint("rating >= 1 AND rating <= 5", name="chk_chatbot_rating_range"),
    )

    message: Mapped["ChatMessage"] = relationship("ChatMessage", back_populates="feedbacks")
    user: Mapped["User"] = relationship("User")

