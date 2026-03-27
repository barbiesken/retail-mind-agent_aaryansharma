"""
Conversation memory handler for RetailMind Agent.
Implements a simple sliding-window list to store conversation history.
"""

# In-memory conversation history store
conversation_history = []

# Maximum messages to retain (sliding window to avoid token overflow)
MAX_HISTORY = 10


def add_message(role: str, content: str):
    """Add a message to conversation history and enforce sliding window."""
    conversation_history.append({"role": role, "content": content})
    # Trim to last MAX_HISTORY messages
    while len(conversation_history) > MAX_HISTORY:
        conversation_history.pop(0)


def get_history() -> list:
    """Return a copy of the current conversation history."""
    return conversation_history.copy()


def clear_memory():
    """Clear all conversation history."""
    conversation_history.clear()
