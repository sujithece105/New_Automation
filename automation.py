import docker
import paramiko
import psutil
import os
import shutil
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SystemManager:
    def __init__(self, ssh_host, ssh_username, ssh_password):
        self.docker_client = docker.from_env()
        self.ssh_host = '3.85.159.160'
        self.ssh_username = 'ec2-user'
        self.ssh_password = 'password'
        
    def create_docker_container(self, image_name, container_name):
        """Create a Docker container"""
        try:
            container = self.docker_client.containers.run(
                image_name,
                name=container_name,
                detach=True
            )
            logger.info(f"Container created successfully: {container_name}")
            return container
        except docker.errors.APIError as e:
            logger.error(f"Failed to create container: {e}")
            return None

    def delete_docker_container(self, container_name):
        """Delete a Docker container"""
        try:
            container = self.docker_client.containers.get(container_name)
            container.remove(force=True)
            logger.info(f"Container deleted successfully: {container_name}")
        except docker.errors.NotFound:
            logger.error(f"Container not found: {container_name}")

    def ssh_connect(self):
        """Establish SSH connection"""
        try:
            ssh_client = paramiko.SSHClient()
            ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh_client.connect(
                self.ssh_host,
                username=self.ssh_username,
                password=self.ssh_password
            )
            logger.info("SSH connection established successfully")
            return ssh_client
        except paramiko.AuthenticationException:
            logger.error("SSH authentication failed")
            return None
        except Exception as e:
            logger.error(f"SSH connection failed: {e}")
            return None

    def get_network_info(self):
        """Get network information"""
        network_info = {}
        
        # Get network interfaces
        interfaces = psutil.net_if_addrs()
        
        for interface, addrs in interfaces.items():
            for addr in addrs:
                if addr.family == 2:  # IPv4
                    network_info[interface] = {
                        'ip': addr.address,
                        'netmask': addr.netmask
                    }
        
        return network_info

    def get_memory_info(self):
        """Get memory information"""
        memory = psutil.virtual_memory()
        return {
            'total': memory.total,
            'available': memory.available,
            'used': memory.used,
            'free': memory.free,
            'percent': memory.percent
        }

    def clean_memory(self, threshold_percent=80):
        """Clean memory if usage exceeds threshold"""
        memory_info = self.get_memory_info()
        
        if memory_info['percent'] > threshold_percent:
            logger.info("Memory usage high. Starting cleanup...")
            
            # Clean temporary files
            self._clean_temp_files()
            
            # Clean Docker system
            self._clean_docker_system()
            
            # Clear system cache (Linux only)
            self._clear_system_cache()
            
            logger.info("Memory cleanup completed")
            return True
        return False

    def _clean_temp_files(self):
        """Clean temporary files"""
        temp_dirs = ['/tmp', os.path.expanduser('~/.cache')]
        for temp_dir in temp_dirs:
            if os.path.exists(temp_dir):
                try:
                    shutil.rmtree(temp_dir)
                    os.makedirs(temp_dir)
                    logger.info(f"Cleaned temporary directory: {temp_dir}")
                except Exception as e:
                    logger.error(f"Failed to clean {temp_dir}: {e}")

    def _clean_docker_system(self):
        """Clean Docker system"""
        try:
            self.docker_client.containers.prune()
            self.docker_client.images.prune()
            self.docker_client.volumes.prune()
            logger.info("Docker system cleaned")
        except Exception as e:
            logger.error(f"Failed to clean Docker system: {e}")

    def _clear_system_cache(self):
        """Clear system cache (Linux only)"""
        if os.name == 'posix':
            try:
                os.system('sync; echo 3 > /proc/sys/vm/drop_caches')
                logger.info("System cache cleared")
            except Exception as e:
                logger.error(f"Failed to clear system cache: {e}")

def main():
    # Initialize system manager
    manager = SystemManager(
        ssh_host='your_host',
        ssh_username='your_username',
        ssh_password='your_password'
    )

    # Create a Docker container
    container = manager.create_docker_container('nginx:latest', 'test-container')

    # Get network information
    network_info = manager.get_network_info()
    logger.info(f"Network information: {network_info}")

    # Get memory information
    memory_info = manager.get_memory_info()
    logger.info(f"Memory information: {memory_info}")

    # Clean memory if needed
    if manager.clean_memory(threshold_percent=80):
        logger.info("Memory cleanup was performed")

    # Delete the Docker container
    manager.delete_docker_container('test-container')

    # Establish SSH connection
    ssh_client = manager.ssh_connect()
    if ssh_client:
        ssh_client.close()

if __name__ == "__main__":
    main()
