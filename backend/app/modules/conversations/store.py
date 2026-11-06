"""In-memory conversation storage for the scaffold.

Replace with SQLAlchemy repositories and Alembic migrations before any real
deployment. Data is lost on process restart; no image bytes are stored.
"""

from dataclasses import dataclass, field
from threading import Lock

from app.modules.conversations.models import Conversation, Message


@dataclass
class _ConversationRecord:
    conversation: Conversation
    messages: list[Message] = field(default_factory=list)
    idempotency: dict[str, tuple[str, str]] = field(default_factory=dict)


class ConversationStore:
    """Process-local store. Not for production use."""

    def __init__(self) -> None:
        self._records: dict[str, _ConversationRecord] = {}
        self._lock = Lock()

    def create(self, conversation: Conversation) -> Conversation:
        with self._lock:
            self._records[conversation.conversation_id] = _ConversationRecord(
                conversation=conversation
            )
            return conversation

    def get(self, conversation_id: str) -> _ConversationRecord | None:
        with self._lock:
            return self._records.get(conversation_id)

    def list_for_owner(self, owner_id: str) -> list[Conversation]:
        with self._lock:
            items = [
                record.conversation
                for record in self._records.values()
                if record.conversation.owner_id == owner_id
            ]
        return sorted(items, key=lambda item: item.last_message_at, reverse=True)

    def delete(self, conversation_id: str) -> bool:
        with self._lock:
            return self._records.pop(conversation_id, None) is not None

    def find_by_client_id(
        self, conversation_id: str, client_message_id: str
    ) -> tuple[str, str] | None:
        with self._lock:
            record = self._records.get(conversation_id)
            if record is None:
                return None
            return record.idempotency.get(client_message_id)

    def append(
        self,
        conversation_id: str,
        messages: list[Message],
        client_message_id: str,
    ) -> None:
        with self._lock:
            record = self._records[conversation_id]
            record.messages.extend(messages)
            record.idempotency[client_message_id] = (
                messages[0].message_id,
                messages[1].message_id,
            )
            record.conversation = record.conversation.model_copy(
                update={"last_message_at": messages[-1].created_at}
            )

    def messages(self, conversation_id: str) -> list[Message]:
        with self._lock:
            record = self._records.get(conversation_id)
            if record is None:
                return []
            return list(record.messages)

    def message(self, conversation_id: str, message_id: str) -> Message | None:
        with self._lock:
            record = self._records.get(conversation_id)
            if record is None:
                return None
            for message in record.messages:
                if message.message_id == message_id:
                    return message
            return None


store = ConversationStore()
