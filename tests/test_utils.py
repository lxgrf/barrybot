"""Unit tests for utils.py utility functions."""
import pytest
from unittest.mock import Mock, MagicMock, patch
import sys

# Mock modules before importing utils
discord_mock = MagicMock()
anthropic_mock = MagicMock()
sys.modules['discord'] = discord_mock
sys.modules['anthropic'] = anthropic_mock

# Create a real Embed class for testing
class MockEmbed:
    def __init__(self, title=None, description=None, **kwargs):
        self.title = title
        self.description = description
        self.kwargs = kwargs

discord_mock.Embed = MockEmbed

# Now we can import
import config
from utils import _server_error, _authorised_user, _ai_enabled_server, get_recent_messages_reversed


class TestServerError:
    """Tests for _server_error function."""
    
    def test_server_error_returns_embed(self):
        """Test that _server_error returns a Discord Embed."""
        # Create a mock context with a guild
        mock_ctx = Mock()
        mock_ctx.guild.id = 123456789
        
        result = _server_error(mock_ctx)
        
        # Check that result is a MockEmbed with correct properties
        assert isinstance(result, MockEmbed)
        assert result.title == "Error - Server not recognised."
        assert str(mock_ctx.guild.id) in result.description
        assert "@lxgrf" in result.description


class TestAuthorisedUser:
    """Tests for _authorised_user function."""
    
    def test_authorised_user_returns_embed(self):
        """Test that _authorised_user returns a Discord Embed."""
        result = _authorised_user()
        
        # Check that result is a MockEmbed with correct properties
        assert isinstance(result, MockEmbed)
        assert result.title == "Error - User not authorised."
        assert "restricted to authorised users" in result.description
        assert "@lxgrf" in result.description


class TestAIEnabledServer:
    """Tests for _ai_enabled_server function."""
    
    def test_ai_enabled_server_with_enabled_server(self):
        """Test that AI-enabled servers return True."""
        # Test with known enabled servers from config
        for guild_id in config.ai_enabled_servers:
            result = _ai_enabled_server(int(guild_id))
            assert result is True, f"Guild {guild_id} should be AI-enabled"
    
    def test_ai_enabled_server_with_disabled_server(self):
        """Test that non-enabled servers return False."""
        # Use a guild ID that's definitely not in the list
        fake_guild_id = 999999999999999999
        result = _ai_enabled_server(fake_guild_id)
        assert result is False
    
    def test_ai_enabled_server_with_string_id(self):
        """Test that string guild IDs work correctly."""
        # config.ai_enabled_servers contains string IDs
        if config.ai_enabled_servers:
            test_id = config.ai_enabled_servers[0]
            result = _ai_enabled_server(test_id)
            assert result is True


class TestGetRecentMessagesReversed:
    """Tests for get_recent_messages_reversed async function."""
    
    @pytest.mark.asyncio
    async def test_get_recent_messages_default_order(self):
        """Test that messages are returned in correct order."""
        # Create mock messages
        mock_messages = [Mock(id=i, content=f"Message {i}") for i in range(5)]
        
        # Create a mock channel with async history
        mock_channel = Mock()
        
        def make_history(limit=25):
            async def mock_history():
                for i in range(min(limit, len(mock_messages))):
                    yield mock_messages[i]
            return mock_history()
        
        mock_channel.history = make_history
        
        result = await get_recent_messages_reversed(mock_channel, limit=5)
        
        assert len(result) == 5
        # Messages should be in the same order as returned (most recent first by default)
        assert result[0].id == 0
        assert result[4].id == 4
    
    @pytest.mark.asyncio
    async def test_get_recent_messages_with_limit(self):
        """Test that limit parameter is respected."""
        mock_messages = [Mock(id=i) for i in range(10)]
        
        mock_channel = Mock()
        
        # Mock the history method to create a fresh generator each time it's called
        def make_history(limit=25):
            async def mock_history():
                for i in range(min(limit, len(mock_messages))):
                    yield mock_messages[i]
            return mock_history()
        
        mock_channel.history = make_history
        
        result = await get_recent_messages_reversed(mock_channel, limit=3)
        
        assert len(result) == 3
    
    @pytest.mark.asyncio
    async def test_get_recent_messages_empty_channel(self):
        """Test behavior with an empty channel."""
        mock_channel = Mock()
        
        def make_history(limit=25):
            async def mock_history():
                return
                yield  # Make it a generator
            return mock_history()
        
        mock_channel.history = make_history
        
        result = await get_recent_messages_reversed(mock_channel, limit=5)
        
        assert isinstance(result, list)
        assert len(result) == 0
