import asyncio
import os
import subprocess
import logging
import paramiko
from typing import Tuple, Optional
from app.config import settings

logger = logging.getLogger("vickyops.ssh")

class SSHManager:
    _instance: Optional["SSHManager"] = None

    def __init__(self):
        self.host = settings.SSH_HOST
        self.port = settings.SSH_PORT
        self.user = settings.SSH_USER
        self.password = settings.SSH_PASSWORD
        self.key_path = settings.SSH_KEY_PATH
        self.timeout = settings.SSH_TIMEOUT
        self.has_docker_sock = os.path.exists("/var/run/docker.sock")
        self.host_proc = os.getenv("HOST_PROC", "")

    @classmethod
    def get_instance(cls) -> "SSHManager":
        if cls._instance is None:
            cls._instance = SSHManager()
        return cls._instance

    def _execute_local(self, command: str, timeout: int = 45) -> Tuple[int, str, str]:
        """Execute command locally inside the container accessing /var/run/docker.sock."""
        # If /host/proc is mounted, adjust /proc paths in command
        cmd = command
        if self.host_proc and os.path.exists(self.host_proc):
            cmd = cmd.replace("/proc/loadavg", f"{self.host_proc}/loadavg")
            cmd = cmd.replace("/proc/net/dev", f"{self.host_proc}/net/dev")

        try:
            res = subprocess.run(
                ["bash", "-c", cmd],
                capture_output=True,
                text=True,
                timeout=timeout
            )
            return res.returncode, res.stdout, res.stderr
        except subprocess.TimeoutExpired:
            return -1, "", "Command timed out"
        except Exception as e:
            return -1, "", str(e)

    def _connect_ssh(self) -> paramiko.SSHClient:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        expanded_key = os.path.expanduser(self.key_path) if self.key_path else None
        
        # Try key first if it exists
        if expanded_key and os.path.exists(expanded_key):
            try:
                client.connect(
                    hostname=self.host,
                    port=self.port,
                    username=self.user,
                    key_filename=expanded_key,
                    timeout=self.timeout
                )
                return client
            except Exception as e:
                logger.warning(f"Key authentication failed: {e}. Falling back to password.")
        
        # Fallback to password
        client.connect(
            hostname=self.host,
            port=self.port,
            username=self.user,
            password=self.password,
            timeout=self.timeout
        )
        return client

    def execute_command_sync(self, command: str, timeout: int = 45) -> Tuple[int, str, str]:
        """
        Execute command on the server.
        If running inside a container on the host with /var/run/docker.sock mounted,
        it uses direct local execution for instant, zero-overhead response.
        Otherwise connects via SSH with password / private key.
        """
        # If running on the host with docker socket mounted, prefer direct local execution
        if self.has_docker_sock:
            code, out, err = self._execute_local(command, timeout)
            if code == 0:
                return code, out, err
            # If local command didn't succeed, fall through to try SSH
            logger.debug(f"Local command returned {code}, trying SSH: {err}")

        # SSH execution
        client = None
        try:
            client = self._connect_ssh()
            stdin, stdout, stderr = client.exec_command(command, timeout=timeout)
            out = stdout.read().decode("utf-8", errors="replace")
            err = stderr.read().decode("utf-8", errors="replace")
            exit_code = stdout.channel.recv_exit_status()
            return exit_code, out, err
        except Exception as e:
            logger.warning(f"SSH execution error: {e}")
            # If SSH fails and we haven't tried local yet, try local as fallback
            if not self.has_docker_sock:
                return self._execute_local(command, timeout)
            return -1, "", str(e)
        finally:
            if client:
                try:
                    client.close()
                except Exception:
                    pass

    async def execute_command(self, command: str, timeout: int = 45) -> Tuple[int, str, str]:
        """Run command asynchronously in a threadpool executor."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.execute_command_sync, command, timeout)

    async def test_connection(self) -> bool:
        exit_code, out, err = await self.execute_command("echo VICKYOPS_OK", timeout=5)
        return exit_code == 0 and "VICKYOPS_OK" in out

ssh_manager = SSHManager.get_instance()
