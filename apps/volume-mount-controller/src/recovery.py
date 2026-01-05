"""
Volume Mount Recovery

Handles recovery and remediation of unhealthy volume mounts.
"""

import os
import time
import logging
import subprocess
from typing import Optional


logger = logging.getLogger(__name__)


class VolumeRecovery:
    """Recover unhealthy volume mounts."""
    
    def __init__(self, timeout: int = 60):
        """
        Initialize recovery handler.
        
        Args:
            timeout: Recovery operation timeout in seconds
        """
        self.timeout = timeout
    
    def recover_mount(self, mount_path: str) -> bool:
        """
        Attempt to recover a mount point.
        
        Args:
            mount_path: Path to the mount point
            
        Returns:
            True if recovery successful, False otherwise
        """
        logger.info(f"Starting recovery for mount {mount_path}")
        
        try:
            # Try unmounting
            logger.info(f"Attempting to unmount {mount_path}...")
            if not self.unmount(mount_path):
                logger.warning(f"Failed to unmount {mount_path}, attempting forced unmount...")
                if not self.unmount(mount_path, force=True):
                    logger.error(f"Could not unmount {mount_path}")
                    return False
            
            # Wait a bit
            time.sleep(1)
            
            # Try remounting
            logger.info(f"Attempting to remount {mount_path}...")
            if not self.remount(mount_path):
                logger.error(f"Failed to remount {mount_path}")
                return False
            
            # Validate recovery
            time.sleep(1)
            if not self.validate_recovery(mount_path):
                logger.error(f"Recovery validation failed for {mount_path}")
                return False
            
            logger.info(f"Successfully recovered mount {mount_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error during recovery of {mount_path}: {e}", exc_info=True)
            return False
    
    def unmount(self, mount_path: str, force: bool = False) -> bool:
        """
        Unmount a volume.
        
        Args:
            mount_path: Path to unmount
            force: Force unmount if True
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not self._is_mounted(mount_path):
                logger.info(f"{mount_path} is not mounted")
                return True
            
            cmd = ['umount', mount_path]
            if force:
                cmd.append('-f')
            
            logger.debug(f"Running: {' '.join(cmd)}")
            result = subprocess.run(
                cmd,
                capture_output=True,
                timeout=self.timeout,
                text=True
            )
            
            if result.returncode == 0:
                logger.info(f"Successfully unmounted {mount_path}")
                return True
            else:
                logger.error(f"Unmount failed: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error(f"Unmount timed out for {mount_path}")
            return False
        except Exception as e:
            logger.error(f"Error unmounting {mount_path}: {e}")
            return False
    
    def remount(self, mount_path: str) -> bool:
        """
        Remount a volume.
        
        Args:
            mount_path: Path to remount
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get mount details from /proc/mounts
            mount_info = self._get_mount_info(mount_path)
            if not mount_info:
                logger.error(f"Could not get mount info for {mount_path}")
                return False
            
            device, fstype, options = mount_info
            
            cmd = ['mount', '-t', fstype, '-o', options, device, mount_path]
            
            logger.debug(f"Running: {' '.join(cmd)}")
            result = subprocess.run(
                cmd,
                capture_output=True,
                timeout=self.timeout,
                text=True
            )
            
            if result.returncode == 0:
                logger.info(f"Successfully remounted {mount_path}")
                return True
            else:
                logger.error(f"Remount failed: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error(f"Remount timed out for {mount_path}")
            return False
        except Exception as e:
            logger.error(f"Error remounting {mount_path}: {e}")
            return False
    
    def validate_recovery(self, mount_path: str) -> bool:
        """
        Validate that recovery was successful.
        
        Args:
            mount_path: Path to validate
            
        Returns:
            True if mount is healthy, False otherwise
        """
        try:
            if not self._is_mounted(mount_path):
                logger.error(f"Mount {mount_path} is not mounted after recovery")
                return False
            
            if not os.access(mount_path, os.R_OK | os.W_OK):
                logger.error(f"Mount {mount_path} is not accessible after recovery")
                return False
            
            logger.info(f"Mount {mount_path} validated successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error validating mount {mount_path}: {e}")
            return False
    
    def _is_mounted(self, mount_path: str) -> bool:
        """Check if a path is mounted."""
        try:
            with open('/proc/mounts', 'r') as f:
                for line in f:
                    parts = line.split()
                    if len(parts) >= 2 and parts[1] == mount_path:
                        return True
            return False
        except Exception as e:
            logger.warning(f"Error checking if mounted: {e}")
            return False
    
    def _get_mount_info(self, mount_path: str) -> Optional[tuple]:
        """Get mount information from /proc/mounts."""
        try:
            with open('/proc/mounts', 'r') as f:
                for line in f:
                    parts = line.split()
                    if len(parts) >= 4 and parts[1] == mount_path:
                        device = parts[0]
                        fstype = parts[2]
                        options = parts[3]
                        return (device, fstype, options)
            return None
        except Exception as e:
            logger.error(f"Error reading mount info: {e}")
            return None
