"""Sandbox manager for secure file operations."""

from __future__ import annotations

import asyncio
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class SandboxConfig:
    """Configuration for sandbox environment."""
    allowed_paths: list[Path] = field(default_factory=list)
    max_file_size: int = 100 * 1024 * 1024  # 100MB
    allowed_extensions: set[str] = field(default_factory=lambda: {
        ".txt", ".md", ".json", ".yaml", ".yml",
        ".py", ".js", ".ts", ".html", ".css",
        ".csv", ".xml", ".log", ".sh", ".bat",
    })
    blocked_extensions: set[str] = field(default_factory=lambda: {
        ".exe", ".dll", ".so", ".dylib",
        ".bin", ".dat",
    })
    use_docker: bool = False
    docker_image: str = "python:3.11-slim"
    docker_timeout: int = 300


class SandboxManager:
    """
    Manages a secure sandbox for file operations.
    
    Features:
    - Path validation and restriction
    - File size limits
    - Extension filtering
    """
    
    def __init__(self, config: SandboxConfig | None = None):
        self.config = config or SandboxConfig()
        self._initialized = False
    
    def add_allowed_path(self, path: str | Path) -> None:
        """Add a path to the allowed list."""
        path = Path(path).resolve()
        if path not in self.config.allowed_paths:
            self.config.allowed_paths.append(path)
    
    def remove_allowed_path(self, path: str | Path) -> None:
        """Remove a path from the allowed list."""
        path = Path(path).resolve()
        if path in self.config.allowed_paths:
            self.config.allowed_paths.remove(path)
    
    def is_path_allowed(self, path: str | Path) -> bool:
        """Check if a path is within allowed paths."""
        path = Path(path).resolve()
        
        if not self.config.allowed_paths:
            return False
        
        return any(
            path == allowed or allowed in path.parents or path in allowed.parents
            for allowed in self.config.allowed_paths
        )
    
    def is_extension_allowed(self, path: str | Path) -> bool:
        """Check if file extension is allowed."""
        path = Path(path)
        ext = path.suffix.lower()
        
        if ext in self.config.blocked_extensions:
            return False
        
        if self.config.allowed_extensions:
            return ext in self.config.allowed_extensions or ext == ""
        
        return True
    
    def validate_path(self, path: str | Path) -> tuple[bool, str | None]:
        """
        Validate a path for sandbox access.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        path = Path(path).resolve()
        
        if not self.is_path_allowed(path):
            return False, f"Path not in allowed directories: {path}"
        
        if path.exists() and path.is_file():
            if not self.is_extension_allowed(path):
                return False, f"File extension not allowed: {path.suffix}"
            
            if path.stat().st_size > self.config.max_file_size:
                return False, f"File exceeds size limit: {path.stat().st_size} bytes"
        
        return True, None
    
    def get_status(self) -> dict[str, Any]:
        """Get sandbox status information."""
        return {
            "allowed_paths": [str(p) for p in self.config.allowed_paths],
            "max_file_size": self.config.max_file_size,
            "allowed_extensions": list(self.config.allowed_extensions),
            "blocked_extensions": list(self.config.blocked_extensions),
            "docker_enabled": self.config.use_docker,
            "docker_available": self._check_docker_available(),
        }
    
    def _check_docker_available(self) -> bool:
        """Check if Docker is available on the system."""
        return shutil.which("docker") is not None
    
    async def run_in_docker(
        self,
        command: str,
        working_dir: str | None = None,
        timeout: int | None = None,
    ) -> tuple[bool, str, str]:
        """
        Run a command inside a Docker container.
        
        Args:
            command: Command to execute
            working_dir: Working directory inside container
            timeout: Execution timeout
            
        Returns:
            Tuple of (success, stdout, stderr)
        """
        if not self._check_docker_available():
            return False, "", "Docker is not available"
        
        timeout = timeout or self.config.docker_timeout
        
        volume_mounts = []
        for path in self.config.allowed_paths:
            mount_path = f"/workspace/{path.name}"
            volume_mounts.extend(["-v", f"{path}:{mount_path}:rw"])
        
        docker_cmd = [
            "docker", "run",
            "--rm",
            "--network", "none",
            "--memory", "512m",
            "--cpus", "1",
            *volume_mounts,
            "-w", working_dir or "/workspace",
            self.config.docker_image,
            "sh", "-c", command,
        ]
        
        try:
            process = await asyncio.create_subprocess_exec(
                *docker_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout
                )
            except asyncio.TimeoutError:
                process.kill()
                return False, "", f"Docker execution timed out after {timeout}s"
            
            return (
                process.returncode == 0,
                stdout.decode("utf-8", errors="replace"),
                stderr.decode("utf-8", errors="replace"),
            )
            
        except Exception as e:
            return False, "", str(e)


class DockerSandbox:
    """
    Docker-based sandbox for isolated code execution.
    
    Provides complete isolation using Docker containers with:
    - Network isolation
    - Resource limits (CPU, memory)
    - Volume mounting for allowed paths only
    """
    
    def __init__(
        self,
        image: str = "python:3.11-slim",
        memory_limit: str = "512m",
        cpu_limit: str = "1",
        network: str = "none",
    ):
        self.image = image
        self.memory_limit = memory_limit
        self.cpu_limit = cpu_limit
        self.network = network
        self._container_id: str | None = None
    
    @property
    def is_available(self) -> bool:
        """Check if Docker is available."""
        return shutil.which("docker") is not None
    
    async def execute(
        self,
        code: str,
        language: str = "python",
        timeout: int = 30,
        volumes: dict[str, str] | None = None,
    ) -> tuple[bool, str, str]:
        """
        Execute code in a Docker container.
        
        Args:
            code: Code to execute
            language: Programming language (python, bash)
            timeout: Execution timeout
            volumes: Volume mappings {host_path: container_path}
            
        Returns:
            Tuple of (success, stdout, stderr)
        """
        if not self.is_available:
            return False, "", "Docker is not available"
        
        if language == "python":
            cmd = ["python3", "-c", code]
        elif language == "bash":
            cmd = ["sh", "-c", code]
        else:
            return False, "", f"Unsupported language: {language}"
        
        docker_cmd = [
            "docker", "run",
            "--rm",
            "--network", self.network,
            "--memory", self.memory_limit,
            "--cpus", self.cpu_limit,
        ]
        
        if volumes:
            for host, container in volumes.items():
                docker_cmd.extend(["-v", f"{host}:{container}:rw"])
        
        docker_cmd.extend([self.image, *cmd])
        
        try:
            process = await asyncio.create_subprocess_exec(
                *docker_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout
                )
            except asyncio.TimeoutError:
                process.kill()
                return False, "", f"Execution timed out after {timeout}s"
            
            return (
                process.returncode == 0,
                stdout.decode("utf-8", errors="replace"),
                stderr.decode("utf-8", errors="replace"),
            )
            
        except Exception as e:
            return False, "", str(e)
