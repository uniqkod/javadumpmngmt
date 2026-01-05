"""Tests for volume mount monitoring."""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from monitor import VolumeMonitor


class TestVolumeMonitor:
    """Tests for VolumeMonitor class."""
    
    @pytest.fixture
    def monitor(self):
        """Create monitor instance."""
        return VolumeMonitor()
    
    def test_check_mount_healthy(self, monitor, tmp_path):
        """Test checking a healthy mount."""
        # mount is healthy if path exists and has permissions
        result = monitor.check_mount(str(tmp_path))
        assert result is True
    
    def test_check_mount_nonexistent(self, monitor):
        """Test checking a non-existent mount."""
        result = monitor.check_mount('/nonexistent/path')
        assert result is False
    
    def test_check_filesystem(self, monitor, tmp_path):
        """Test filesystem health check."""
        result = monitor.check_filesystem(str(tmp_path))
        assert result is not None
        assert 'total' in result
        assert 'used' in result
        assert 'free' in result
        assert 'percent' in result
    
    def test_check_filesystem_invalid(self, monitor):
        """Test filesystem check with invalid path."""
        result = monitor.check_filesystem('/nonexistent/path')
        assert result is None
