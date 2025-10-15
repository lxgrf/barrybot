"""Unit tests for config.py validation."""
import pytest
import config


class TestConfigStructure:
    """Tests for validating config.py structure."""
    
    def test_guilds_dict_exists(self):
        """Test that guilds dictionary is defined."""
        assert hasattr(config, 'guilds')
        assert isinstance(config.guilds, dict)
    
    def test_guilds_have_string_keys(self):
        """Test that guild IDs are strings."""
        for guild_id in config.guilds.keys():
            assert isinstance(guild_id, str), f"Guild ID {guild_id} should be a string"
    
    def test_guilds_have_string_values(self):
        """Test that guild descriptions are strings."""
        for description in config.guilds.values():
            assert isinstance(description, str), f"Guild description should be a string"


class TestAIGuilds:
    """Tests for AI guilds configuration."""
    
    def test_ai_guilds_dict_exists(self):
        """Test that ai_guilds dictionary is defined."""
        assert hasattr(config, 'ai_guilds')
        assert isinstance(config.ai_guilds, dict)
    
    def test_ai_guilds_subset_of_guilds(self):
        """Test that all AI guilds are in the guilds list."""
        for guild_id in config.ai_guilds.keys():
            assert guild_id in config.guilds, f"AI guild {guild_id} should be in guilds list"


class TestUserRoles:
    """Tests for user role configuration."""
    
    def test_include_role_is_list(self):
        """Test that include_role is a list."""
        assert hasattr(config, 'include_role')
        assert isinstance(config.include_role, list)
    
    def test_exclude_role_is_list(self):
        """Test that exclude_role is a list."""
        assert hasattr(config, 'exclude_role')
        assert isinstance(config.exclude_role, list)
    
    def test_authorised_roles_is_list(self):
        """Test that authorised_roles is a list."""
        assert hasattr(config, 'authorised_roles')
        assert isinstance(config.authorised_roles, list)
    
    def test_include_role_not_empty(self):
        """Test that include_role has at least one role."""
        assert len(config.include_role) > 0


class TestActivityThresholds:
    """Tests for activity threshold configuration."""
    
    def test_inactivity_threshold_is_positive(self):
        """Test that inactivity_threshold is a positive integer."""
        assert hasattr(config, 'inactivity_threshold')
        assert isinstance(config.inactivity_threshold, int)
        assert config.inactivity_threshold > 0
    
    def test_warning_threshold_is_positive(self):
        """Test that warning_threshold is a positive integer."""
        assert hasattr(config, 'warning_threshold')
        assert isinstance(config.warning_threshold, int)
        assert config.warning_threshold > 0
    
    def test_warning_threshold_less_than_inactivity(self):
        """Test that warning_threshold is less than inactivity_threshold."""
        assert config.warning_threshold < config.inactivity_threshold


class TestMonitoredChannels:
    """Tests for monitored channels configuration."""
    
    def test_monitored_channels_dict_exists(self):
        """Test that monitored_channels dictionary is defined."""
        assert hasattr(config, 'monitored_channels')
        assert isinstance(config.monitored_channels, dict)
    
    def test_monitored_channels_are_integers(self):
        """Test that all guild IDs are integers."""
        for guild_id in config.monitored_channels.keys():
            assert isinstance(guild_id, int), f"Guild ID {guild_id} should be an integer"
    
    def test_monitored_channels_values_are_lists(self):
        """Test that all monitored channel values are lists."""
        for guild_id, channels in config.monitored_channels.items():
            assert isinstance(channels, list), f"Channels for guild {guild_id} should be a list"
    
    def test_monitored_channel_ids_are_integers(self):
        """Test that all channel IDs are integers."""
        for guild_id, channels in config.monitored_channels.items():
            for channel_id in channels:
                assert isinstance(channel_id, int), f"Channel ID {channel_id} in guild {guild_id} should be an integer"


class TestChannelTimes:
    """Tests for channel times configuration."""
    
    def test_channeltimes_dict_exists(self):
        """Test that channeltimes dictionary is defined."""
        assert hasattr(config, 'channeltimes')
        assert isinstance(config.channeltimes, dict)
    
    def test_channeltimes_have_yellow_and_red(self):
        """Test that each guild has yellow and red thresholds."""
        for guild_id, times in config.channeltimes.items():
            assert 'yellow' in times, f"Guild {guild_id} should have 'yellow' threshold"
            assert 'red' in times, f"Guild {guild_id} should have 'red' threshold"
    
    def test_channeltimes_are_positive_integers(self):
        """Test that all time thresholds are positive integers."""
        for guild_id, times in config.channeltimes.items():
            assert isinstance(times['yellow'], int), f"Yellow threshold for guild {guild_id} should be int"
            assert isinstance(times['red'], int), f"Red threshold for guild {guild_id} should be int"
            assert times['yellow'] > 0, f"Yellow threshold for guild {guild_id} should be positive"
            assert times['red'] > 0, f"Red threshold for guild {guild_id} should be positive"
    
    def test_channeltimes_red_greater_than_yellow(self):
        """Test that red threshold is greater than or equal to yellow."""
        for guild_id, times in config.channeltimes.items():
            assert times['red'] >= times['yellow'], \
                f"Red threshold should be >= yellow threshold for guild {guild_id}"


class TestAIEnabledServers:
    """Tests for AI enabled servers configuration."""
    
    def test_ai_enabled_servers_is_list(self):
        """Test that ai_enabled_servers is a list."""
        assert hasattr(config, 'ai_enabled_servers')
        assert isinstance(config.ai_enabled_servers, list)
    
    def test_ai_enabled_servers_are_strings(self):
        """Test that all AI enabled server IDs are strings."""
        for server_id in config.ai_enabled_servers:
            assert isinstance(server_id, str), f"Server ID {server_id} should be a string"


class TestOptInRoles:
    """Tests for opt-in roles configuration."""
    
    def test_opt_in_roles_dict_exists(self):
        """Test that opt_in_roles dictionary is defined."""
        assert hasattr(config, 'opt_in_roles')
        assert isinstance(config.opt_in_roles, dict)
    
    def test_opt_in_roles_values_are_strings(self):
        """Test that all opt-in role names are strings."""
        for guild_id, role_name in config.opt_in_roles.items():
            assert isinstance(role_name, str), f"Role name for guild {guild_id} should be a string"


class TestTLDRConfiguration:
    """Tests for TLDR-related configuration."""
    
    def test_tldr_output_channels_dict_exists(self):
        """Test that tldr_output_channels dictionary is defined."""
        assert hasattr(config, 'tldr_output_channels')
        assert isinstance(config.tldr_output_channels, dict)
    
    def test_tldr_excluded_channels_dict_exists(self):
        """Test that tldr_excluded_channels dictionary is defined."""
        assert hasattr(config, 'tldr_excluded_channels')
        assert isinstance(config.tldr_excluded_channels, dict)
    
    def test_tldr_additional_channels_dict_exists(self):
        """Test that tldr_additional_channels dictionary is defined."""
        assert hasattr(config, 'tldr_additional_channels')
        assert isinstance(config.tldr_additional_channels, dict)
