"""
Volume Mount Monitoring

Checks health and accessibility of volume mount points.
"""

import os
import logging
from pathlib import Path
from typing import Optional


logger = logging.getLogger(__name__)


class VolumeMonitor:
    """Monitor volume mount health and accessibility."""
    
    def check_mount(self, mount_path: str) -> bool:
        """
        Check if a mount point is healthy and accessible.
        
        Args:
            mount_path: Path to the mount point
            
        Returns:
            True if mount is healthy, False otherwise
        """
        try:
            path = Path(mount_path)
            
            # Check if path exists
            if not path.exists():
                logger.warning(f"Mount path does not exist: {mount_path}")
                return False
            
            # Check if it's a directory
            if not path.is_dir():
                logger.warning(f"Mount path is not a directory: {mount_path}")
                return False
            
            # Check read permissions
            if not os.access(mount_path, os.R_OK):
                logger.warning(f"No read permission on mount: {mount_path}")
                return False
            
            # Check write permissions
            if not os.access(mount_path, os.W_OK):
                logger.warning(f"No write permission on mount: {mount_path}")
                return False
            
            # Try to read directory listing
            try:
                list(path.iterdir())
            except OSError as e:
                logger.warning(f"Cannot read directory {mount_path}: {e}")
                return False
            
            # Try to create and remove a test file
            test_file = path / '.health-check'
            try:
                test_file.write_text('health-check')
                test_file.unlink()
            except Exception as e:
                logger.warning(f"Cannot write to mount {mount_path}: {e}")
                return False
            
            logger.debug(f"Mount {mount_path} is healthy")
            return True
            
        except Exception as e:
            logger.error(f"Error checking mount {mount_path}: {e}")
            return False
    
    def check_filesystem(self, mount_path: str) -> Optional[dict]:
        """
        Check filesystem health and available space.
        
        Args:
            mount_path: Path to the mount point
            
        Returns:
            Dictionary with filesystem stats or None if error
        """
        try:
            import shutil
            stat = shutil.disk_usage(mount_path)
            
            return {
                'total': stat.total,
                'used': stat.used,
                'free': stat.free,
                'percent': (stat.used / stat.total * 100) if stat.total > 0 else 0,
            }
        except Exception as e:
            logger.error(f"Error checking filesystem for {mount_path}: {e}")
            return None
    
    def check_propagation(self, mount_path: str) -> Optional[str]:
        """
        Check mount propagation mode.
        
        Args:
            mount_path: Path to the mount point
            
        Returns:
            Mount propagation mode or None if error
        """
        try:
            # Try to read /proc/mounts to get mount info
            with open('/proc/mounts', 'r') as f:
                for line in f:
                    parts = line.split()
                    if len(parts) >= 4 and parts[1] == mount_path:
                        options = parts[3].split(',')
                        propagation = [opt for opt in options 
                                     if opt in ['shared', 'slave', 'private', 'rslave', 'rprivate', 'rshared']]
                        return propagation[0] if propagation else 'unknown'
            
            return None
        except Exception as e:
            logger.debug(f"Could not determine mount propagation for {mount_path}: {e}")
            return None
