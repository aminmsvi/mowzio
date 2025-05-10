import pytest

from llm.memory import PersistedWindowBufferMemory, Message
from app.db.redis import FakeRedisAdapter


@pytest.fixture
def fake_redis_client():
    return FakeRedisAdapter()


@pytest.fixture
def memory_ws5(fake_redis_client):  # window_size=5
    return PersistedWindowBufferMemory(window_size=5, redis=fake_redis_client)


@pytest.fixture
def memory_ws2(fake_redis_client):  # window_size=2
    return PersistedWindowBufferMemory(window_size=2, redis=fake_redis_client)


@pytest.fixture
def memory_ws3(fake_redis_client):  # window_size=3
    return PersistedWindowBufferMemory(window_size=3, redis=fake_redis_client)


@pytest.fixture
def user_message():
    return Message(role="user", content="Generic user message")


@pytest.fixture
def assistant_message():
    return Message(role="assistant", content="Generic assistant message")


@pytest.fixture
def system_message():
    return Message(role="system", content="Generic system prompt")


def test_initialization(memory_ws5):
    """Test that WindowBufferedMemory initializes correctly."""
    assert memory_ws5._window_size == 5
    assert memory_ws5.get_messages() == []


def test_add_message_within_window(memory_ws5, user_message, assistant_message):
    """Test adding messages within the window size."""
    memory_ws5.add_message(user_message)
    memory_ws5.add_message(assistant_message)
    assert memory_ws5.get_messages() == [user_message, assistant_message]


def test_add_message_exceeding_window(memory_ws2):  # Changed from sut to memory_ws2
    """Test adding messages that exceed the window size."""
    msg1 = Message(role="user", content="Message 1")
    msg2 = Message(role="assistant", content="Message 2")
    msg3 = Message(role="user", content="Message 3")
    msg4 = Message(role="assistant", content="Message 4")

    memory_ws2.add_message(msg1)
    memory_ws2.add_message(msg2)
    # Window with size 2: [msg1, msg2]
    assert memory_ws2.get_messages() == [msg1, msg2]

    memory_ws2.add_message(msg3)
    # Window: [msg2, msg3]
    assert memory_ws2.get_messages() == [msg2, msg3]

    memory_ws2.add_message(msg4)
    # Window: [msg3, msg4]
    assert memory_ws2.get_messages() == [msg3, msg4]


def test_add_message_with_system_prompt_preserved(memory_ws2, system_message):
    """Test that system prompts are preserved when the window size is exceeded."""
    # system_message is from fixture
    user_msg1 = Message(role="user", content="User message 1")
    assistant_msg1 = Message(role="assistant", content="Assistant message 1")
    user_msg2 = Message(role="user", content="User message 2")

    memory_ws2.add_message(system_message)
    memory_ws2.add_message(user_msg1)
    memory_ws2.add_message(assistant_msg1)
    # History: [system_message, user_msg1, assistant_msg1] (non-system count = 2)
    assert memory_ws2.get_messages() == [system_message, user_msg1, assistant_msg1]

    memory_ws2.add_message(user_msg2)
    # History should now be [system_message, assistant_msg1, user_msg2] because user_msg1 (first non-system) is removed
    assert memory_ws2.get_messages() == [system_message, assistant_msg1, user_msg2]


def test_get_messages_returns_copy(memory_ws2, user_message):
    """Test that get_messages returns a copy, not the original list."""
    memory_ws2.add_message(user_message)
    messages_copy = memory_ws2.get_messages()
    messages_copy.append(Message(role="user", content="Modified"))
    assert memory_ws2.get_messages() == [user_message]  # Original should be unchanged


def test_clear_messages(memory_ws2, system_message, user_message):
    """Test clearing all messages."""
    memory_ws2.add_message(system_message)
    memory_ws2.add_message(user_message)
    memory_ws2.clear_messages()
    assert memory_ws2.get_messages() == []


def test_clear_messages_with_system_prompt(memory_ws2, system_message, user_message):
    """Test clearing messages while preserving a specific system prompt."""
    memory_ws2.add_message(system_message)
    memory_ws2.add_message(user_message)
    memory_ws2.clear_messages(system_prompt=system_message)
    assert memory_ws2.get_messages() == [system_message]


def test_remove_last_message(memory_ws3):
    """Test removing the last message."""
    msg1 = Message(role="user", content="Msg 1")
    msg2 = Message(role="assistant", content="Msg 2")
    memory_ws3.add_message(msg1)
    memory_ws3.add_message(msg2)
    memory_ws3.remove_last_message()
    assert memory_ws3.get_messages() == [msg1]


def test_remove_last_message_when_system(memory_ws2, system_message, user_message):
    """Test that remove_last_message does not remove a system prompt."""
    memory_ws2.add_message(system_message)
    memory_ws2.remove_last_message()  # Try removing system msg
    assert memory_ws2.get_messages() == [system_message]

    memory_ws2.add_message(user_message)
    memory_ws2.remove_last_message()  # Remove user msg
    assert memory_ws2.get_messages() == [system_message]
    memory_ws2.remove_last_message()  # Try removing system msg again
    assert memory_ws2.get_messages() == [system_message]


def test_remove_last_message_empty_history(memory_ws2):
    """Test removing the last message from an empty history."""
    memory_ws2.remove_last_message()
    assert memory_ws2.get_messages() == []
