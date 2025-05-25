"""
Terminal operations for command execution
"""

import subprocess
import os
import shlex
import psutil
from threading import Timer

class TerminalOperations:
    def __init__(self, config, logger):
        self.config = config
        self.logger = logger
        self.allowed_commands = config.get('security.allowed_commands', [])
        self.blocked_commands = config.get('security.blocked_commands', [])
        self.max_output_lines = config.get('security.max_output_lines', 1000)

    def _is_command_allowed(self, command):
        """Check if command is allowed based on security settings"""
        command_lower = command.lower().strip()
        
        # Check blocked commands
        for blocked in self.blocked_commands:
            if blocked.lower() in command_lower:
                return False, f"Command blocked: contains '{blocked}'"
        
        # Check allowed commands
        if self.allowed_commands:
            command_parts = shlex.split(command_lower)
            if command_parts:
                base_command = command_parts[0]
                if base_command not in [cmd.lower() for cmd in self.allowed_commands]:
                    return False, f"Command not allowed: '{base_command}'"
        
        return True, "OK"

    def execute_command(self, command, working_directory="."):
        """Execute terminal command with security checks and timeout"""
        try:
            # Security check
            allowed, message = self._is_command_allowed(command)
            if not allowed:
                return {"success": False, "error": message}
            
            # Validate working directory
            if not os.path.exists(working_directory):
                return {"success": False, "error": f"Working directory not found: {working_directory}"}
            
            if not os.path.isdir(working_directory):
                return {"success": False, "error": f"Working directory is not a directory: {working_directory}"}
            
            self.logger.info(f"Executing command: {command} in {working_directory}")
            
            # Execute command with timeout
            process = subprocess.Popen(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=working_directory,
                env=os.environ.copy()
            )
            
            # Set timeout (30 seconds default)
            timeout = 30
            timer = Timer(timeout, process.kill)
            timer.start()
            
            try:
                stdout, stderr = process.communicate()
                timer.cancel()
            except:
                timer.cancel()
                process.kill()
                return {
                    "success": False,
                    "error": f"Command timed out after {timeout} seconds"
                }
            
            # Limit output lines
            stdout_lines = stdout.split('\n')
            stderr_lines = stderr.split('\n')
            
            if len(stdout_lines) > self.max_output_lines:
                stdout = '\n'.join(stdout_lines[:self.max_output_lines])
                stdout += f"\n... (truncated, showing first {self.max_output_lines} lines)"
            
            if len(stderr_lines) > self.max_output_lines:
                stderr = '\n'.join(stderr_lines[:self.max_output_lines])
                stderr += f"\n... (truncated, showing first {self.max_output_lines} lines)"
            
            return {
                "success": True,
                "command": command,
                "working_directory": working_directory,
                "stdout": stdout,
                "stderr": stderr,
                "return_code": process.returncode,
                "stdout_lines": len(stdout_lines),
                "stderr_lines": len(stderr_lines)
            }
            
        except Exception as e:
            self.logger.error(f"Error executing command '{command}': {str(e)}")
            return {"success": False, "error": str(e)}

    def get_system_info(self):
        """Get basic system information"""
        try:
            return {
                "success": True,
                "cpu_count": psutil.cpu_count(),
                "memory": {
                    "total": psutil.virtual_memory().total,
                    "available": psutil.virtual_memory().available,
                    "percent": psutil.virtual_memory().percent
                },
                "disk": {
                    "total": psutil.disk_usage('/').total,
                    "free": psutil.disk_usage('/').free,
                    "percent": psutil.disk_usage('/').percent
                },
                "load_average": os.getloadavg() if hasattr(os, 'getloadavg') else None
            }
        except Exception as e:
            self.logger.error(f"Error getting system info: {str(e)}")
            return {"success": False, "error": str(e)} 