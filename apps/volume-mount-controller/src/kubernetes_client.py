"""
Kubernetes Client

Interacts with the Kubernetes API for status updates and event logging.
"""

import os
import logging
from typing import Dict, Optional

try:
    from kubernetes import client, config, watch
    from kubernetes.client.rest import ApiException
    K8S_AVAILABLE = True
except ImportError:
    K8S_AVAILABLE = False


logger = logging.getLogger(__name__)


class KubernetesClient:
    """Client for Kubernetes API interactions."""
    
    def __init__(self, namespace: str = 'default'):
        """
        Initialize Kubernetes client.
        
        Args:
            namespace: Kubernetes namespace
        """
        self.namespace = namespace
        self.enabled = K8S_AVAILABLE
        
        if not self.enabled:
            logger.warning("Kubernetes client not available - running in offline mode")
            self.v1 = None
            self.node_name = None
            return
        
        try:
            config.load_incluster_config()
            self.v1 = client.CoreV1Api()
            self.node_name = self._get_node_name_from_env()
            logger.info(f"Kubernetes client initialized for namespace: {namespace}")
        except Exception as e:
            logger.warning(f"Failed to initialize Kubernetes client: {e}")
            self.enabled = False
            self.v1 = None
            self.node_name = None
    
    def get_node_name(self) -> Optional[str]:
        """
        Get the current node name.
        
        Returns:
            Node name or None if not available
        """
        if not self.enabled:
            return os.getenv('NODE_NAME', 'unknown')
        
        return self.node_name
    
    def _get_node_name_from_env(self) -> Optional[str]:
        """Get node name from environment or downward API."""
        node_name = os.getenv('NODE_NAME')
        if node_name:
            return node_name
        
        # Try to get from downward API mounted files
        try:
            with open('/var/run/secrets/kubernetes.io/pod/spec.nodeName', 'r') as f:
                return f.read().strip()
        except:
            pass
        
        return 'unknown'
    
    def update_node_status(self, labels: Dict[str, str]) -> bool:
        """
        Update node labels/annotations with controller status.
        
        Args:
            labels: Dictionary of labels to set on node
            
        Returns:
            True if successful, False otherwise
        """
        if not self.enabled or not self.v1:
            logger.debug("Kubernetes client not available, skipping status update")
            return False
        
        try:
            node_name = self.get_node_name()
            if not node_name:
                logger.warning("No node name available for status update")
                return False
            
            # Patch node with annotations
            body = {
                'metadata': {
                    'labels': labels
                }
            }
            
            self.v1.patch_node(node_name, body)
            logger.debug(f"Updated node {node_name} with labels: {labels}")
            return True
            
        except ApiException as e:
            logger.error(f"API error updating node status: {e}")
            return False
        except Exception as e:
            logger.error(f"Error updating node status: {e}")
            return False
    
    def create_event(self, message: str, event_type: str = 'Normal') -> bool:
        """
        Create an event in the Kubernetes cluster.
        
        Args:
            message: Event message
            event_type: Event type (Normal, Warning, Error)
            
        Returns:
            True if successful, False otherwise
        """
        if not self.enabled or not self.v1:
            logger.debug("Kubernetes client not available, skipping event creation")
            return False
        
        try:
            from datetime import datetime
            
            # Create event object
            event = client.V1Event(
                metadata=client.V1ObjectMeta(
                    name=f"volume-mount-controller-{datetime.now().isoformat()}",
                    namespace=self.namespace
                ),
                type=event_type,
                message=message,
                source=client.V1EventSource(component='volume-mount-controller'),
                involved_object=client.V1ObjectReference(
                    kind='Node',
                    name=self.get_node_name(),
                ),
                first_timestamp=datetime.utcnow(),
                last_timestamp=datetime.utcnow(),
                count=1,
            )
            
            self.v1.create_namespaced_event(self.namespace, event)
            logger.debug(f"Created event: {message}")
            return True
            
        except ApiException as e:
            logger.error(f"API error creating event: {e}")
            return False
        except Exception as e:
            logger.error(f"Error creating event: {e}")
            return False
    
    def get_pod_mounts(self) -> Dict[str, list]:
        """
        Get expected mount points from pod specifications.
        
        Returns:
            Dictionary mapping pod names to their mount paths
        """
        if not self.enabled or not self.v1:
            return {}
        
        try:
            pods = self.v1.list_namespaced_pod(self.namespace)
            mounts = {}
            
            for pod in pods.items:
                pod_mounts = []
                for container in pod.spec.containers or []:
                    for vm in container.volume_mounts or []:
                        pod_mounts.append(vm.mount_path)
                
                if pod_mounts:
                    mounts[pod.metadata.name] = pod_mounts
            
            return mounts
            
        except ApiException as e:
            logger.error(f"API error getting pod mounts: {e}")
            return {}
        except Exception as e:
            logger.error(f"Error getting pod mounts: {e}")
            return {}
