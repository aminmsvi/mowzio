from llm.memory import PersistedWindowMemory, Message


def test_initialization():
    """Test that WindowBufferedMemory initializes correctly."""
    memory = PersistedWindowMemory(window_size=5)
    assert memory._window_size == 5
    assert memory.get_messages() == []


def test_add_message_within_window():
    """Test adding messages within the window size."""
    memory = PersistedWindowMemory(window_size=3)
    msg1 = Message(role="user", content="Hello")
    msg2 = Message(role="assistant", content="Hi there!")
    memory.add_message(msg1)
    memory.add_message(msg2)
    assert memory.get_messages() == [msg1, msg2]


def test_add_message_exceeding_window():
    """Test adding messages that exceed the window size."""
    memory = PersistedWindowMemory(window_size=2)
    msg1 = Message(role="user", content="Message 1")
    msg2 = Message(role="assistant", content="Message 2")
    msg3 = Message(role="user", content="Message 3")
    msg4 = Message(role="assistant", content="Message 4")

    memory.add_message(msg1)
    memory.add_message(msg2)
    memory.add_message(msg3)
    # Window: [msg2, msg3]
    assert memory.get_messages() == [msg2, msg3]

    memory.add_message(msg4)
    # Window: [msg3, msg4]
    assert memory.get_messages() == [msg3, msg4]


def test_add_message_with_system_prompt_preserved():
    """Test that system prompts are preserved when the window size is exceeded."""
    memory = PersistedWindowMemory(window_size=2)
    system_msg = Message(role="system", content="System prompt")
    msg1 = Message(role="user", content="User message 1")
    msg2 = Message(role="assistant", content="Assistant message 1")
    msg3 = Message(role="user", content="User message 2")

    memory.add_message(system_msg)
    memory.add_message(msg1)
    memory.add_message(msg2)
    # History: [system_msg, msg1, msg2] (non-system count = 2)
    assert memory.get_messages() == [system_msg, msg1, msg2]

    memory.add_message(msg3)
    # History should now be [system_msg, msg2, msg3] because msg1 (first non-system) is removed
    assert memory.get_messages() == [system_msg, msg2, msg3]


def test_get_messages_returns_copy():
    """Test that get_messages returns a copy, not the original list."""
    memory = PersistedWindowMemory(window_size=2)
    msg1 = Message(role="user", content="Test")
    memory.add_message(msg1)
    messages_copy = memory.get_messages()
    messages_copy.append(Message(role="user", content="Modified"))
    assert memory.get_messages() == [msg1]  # Original should be unchanged


def test_clear_messages():
    """Test clearing all messages."""
    memory = PersistedWindowMemory(window_size=2)
    memory.add_message(Message(role="system", content="System"))
    memory.add_message(Message(role="user", content="User"))
    memory.clear_messages()
    assert memory.get_messages() == []


def test_clear_messages_with_system_prompt():
    """Test clearing messages while preserving a specific system prompt."""
    memory = PersistedWindowMemory(window_size=2)
    system_msg = Message(role="system", content="System")
    memory.add_message(system_msg)
    memory.add_message(Message(role="user", content="User"))
    memory.clear_messages(system_prompt=system_msg)
    assert memory.get_messages() == [system_msg]


def test_remove_last_message():
    """Test removing the last message."""
    memory = PersistedWindowMemory(window_size=3)
    msg1 = Message(role="user", content="Msg 1")
    msg2 = Message(role="assistant", content="Msg 2")
    memory.add_message(msg1)
    memory.add_message(msg2)
    memory.remove_last_message()
    assert memory.get_messages() == [msg1]


def test_remove_last_message_when_system():
    """Test that remove_last_message does not remove a system prompt."""
    memory = PersistedWindowMemory(window_size=2)
    system_msg = Message(role="system", content="System prompt")
    user_msg = Message(role="user", content="User message")

    memory.add_message(system_msg)
    memory.remove_last_message()  # Try removing system msg
    assert memory.get_messages() == [system_msg]

    memory.add_message(user_msg)
    memory.remove_last_message()  # Remove user msg
    assert memory.get_messages() == [system_msg]
    memory.remove_last_message()  # Try removing system msg again
    assert memory.get_messages() == [system_msg]


def test_remove_last_message_empty_history():
    """Test removing the last message from an empty history."""
    memory = PersistedWindowMemory(window_size=2)
    memory.remove_last_message()
    assert memory.get_messages() == []
