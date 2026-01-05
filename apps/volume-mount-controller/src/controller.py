"""
Main Volume Mount Controller

Orchestrates monitoring and recovery of volume mounts in Kubernetes.
"""

import os
import time
import logging
from typing import List, Dict, Optional
from pathlib import Path

from monitor import VolumeMonitor
from recovery import VolumeRecovery
from kubernetes_client import KubernetesClient


logger = logging.getLogger(__name__)


class VolumeMountController:
    """Main controller for managing volume mount health and recovery."""
    
    def __init__(self):
        """Initialize the controller."""
        self.monitor_interval = int(os.getenv('MONITOR_INTERVAL', '30'))
        self.recovery_timeout = int(os.getenv('RECOVERY_TIMEOUT', '60'))
        self.mount_paths = self._parse_mount_paths()
        self.namespace = os.getenv('NAMESPACE', 'default')
        
        self.monitor = VolumeMonitor()
        self.recovery = VolumeRecovery(timeout=self.recovery_timeout)
        self.k8s_client = KubernetesClient(namespace=self.namespace)
        
        self.running = False
        self.node_name = None
        
        logger.info(f"Controller initialized with {len(self.mount_paths)} mount paths")
        logger.info(f"Monitor interval: {self.monitor_interval}s, Recovery timeout: {self.recovery_timeout}s")
    
    def _parse_mount_paths(self) -> List[str]:
        """Parse mount paths from environment variable."""
        mount_paths_env = os.getenv('MOUNT_PATHS', '/mnt/dump')
        paths = [p.strip() for p in mount_paths_env.split(',') if p.strip()]
        return paths
    
    def start(self) -> None:
        """Start the monitoring loop."""
        self.running = True
        logger.info("Starting monitoring loop...")
        
        try:
            self.node_name = self.k8s_client.get_node_name()
            logger.info(f"Running on node: {self.node_name}")
        except Exception as e:
            logger.error(f"Failed to get node name: {e}")
            self.node_name = "unknown"
        
        iteration = 0
        while self.running:
            try:
                iteration += 1
                logger.debug(f"Monitor iteration {iteration}")
                
                # Check all mounts
                mount_status = self.monitor_mounts()
                
                # Log status
                self._log_status(mount_status)
                
                # Attempt recovery if needed
                if not all(mount_status.values()):
                    self.recover_mounts(mount_status)
                
                # Update node status
                self._update_node_status(mount_status)
                
                # Sleep until next iteration
                time.sleep(self.monitor_interval)
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}", exc_info=True)
                time.sleep(self.monitor_interval)
    
    def stop(self) -> None:
        """Stop the monitoring loop."""
        logger.info("Stopping controller...")
        self.running = False
    
    def monitor_mounts(self) -> Dict[str, bool]:
        """Monitor all configured mount paths."""
        mount_status = {}
        
        for path in self.mount_paths:
            try:
                is_healthy = self.monitor.check_mount(path)
                mount_status[path] = is_healthy
                
                if is_healthy:
                    logger.debug(f"Mount {path} is healthy")
                else:
                    logger.warning(f"Mount {path} is unhealthy")
                    
            except Exception as e:
                logger.error(f"Error checking mount {path}: {e}")
                mount_status[path] = False
        
        return mount_status
    
    def recover_mounts(self, mount_status: Dict[str, bool]) -> None:
        """Attempt to recover unhealthy mounts."""
        unhealthy_mounts = [path for path, healthy in mount_status.items() if not healthy]
        
        for path in unhealthy_mounts:
            try:
                logger.info(f"Attempting to recover mount {path}...")
                success = self.recovery.recover_mount(path)
                
                if success:
                    logger.info(f"Successfully recovered mount {path}")
                    mount_status[path] = True
                else:
                    logger.error(f"Failed to recover mount {path}")
                    
            except Exception as e:
                logger.error(f"Error recovering mount {path}: {e}", exc_info=True)
    
    def _log_status(self, mount_status: Dict[str, bool]) -> None:
        """Log mount status summary."""
        healthy = sum(1 for v in mount_status.values() if v)
        total = len(mount_status)
        logger.info(f"Mount status: {healthy}/{total} healthy")
    
    def _update_node_status(self, mount_status: Dict[str, bool]) -> None:
        """Update node status in Kubernetes."""
        try:
            if not self.node_name:
                return
            
            all_healthy = all(mount_status.values())
            status = "ready" if all_healthy else "unhealthy"
            
            self.k8s_client.update_node_status({
                'mount-controller/status': status,
                'mount-controller/checked-at': str(int(time.time())),
            })
            
        except Exception as e:
            logger.warning(f"Failed to update node status: {e}")
