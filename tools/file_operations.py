"""
File operations tools for Cursor compatibility
"""

import os
import json
import mimetypes
from pathlib import Path

class FileOperations:
    def __init__(self, config, logger):
        self.config = config
        self.logger = logger
        self.max_file_size = config.get('security.max_file_size_mb', 10) * 1024 * 1024
        self.allowed_dirs = config.get('security.allowed_directories', [])
        self.blocked_dirs = config.get('security.blocked_directories', [])

    def _is_path_allowed(self, file_path):
        """Check if file path is allowed based on security settings"""
        abs_path = os.path.abspath(file_path)
        
        # Check blocked directories
        for blocked_dir in self.blocked_dirs:
            if abs_path.startswith(os.path.abspath(blocked_dir)):
                return False, f"Access denied: {blocked_dir} is blocked"
        
        # Check allowed directories
        if self.allowed_dirs:
            allowed = False
            for allowed_dir in self.allowed_dirs:
                if abs_path.startswith(os.path.abspath(allowed_dir)):
                    allowed = True
                    break
            if not allowed:
                return False, "Access denied: Path not in allowed directories"
        
        return True, "OK"

    def read_file(self, file_path):
        """Read file contents with security checks"""
        try:
            # Security check
            allowed, message = self._is_path_allowed(file_path)
            if not allowed:
                return {"success": False, "error": message}
            
            if not os.path.exists(file_path):
                return {"success": False, "error": f"File not found: {file_path}"}
            
            if not os.path.isfile(file_path):
                return {"success": False, "error": f"Path is not a file: {file_path}"}
            
            # Check file size
            file_size = os.path.getsize(file_path)
            if file_size > self.max_file_size:
                return {
                    "success": False, 
                    "error": f"File too large: {file_size} bytes (max: {self.max_file_size})"
                }
            
            # Determine if file is binary
            mime_type, _ = mimetypes.guess_type(file_path)
            is_binary = mime_type and not mime_type.startswith('text/')
            
            if is_binary:
                return {
                    "success": False,
                    "error": f"Cannot read binary file: {file_path} (type: {mime_type})"
                }
            
            # Read file
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Limit output lines
            max_lines = self.config.get('security.max_output_lines', 1000)
            lines = content.split('\n')
            if len(lines) > max_lines:
                content = '\n'.join(lines[:max_lines])
                content += f"\n... (truncated, showing first {max_lines} lines)"
            
            return {
                "success": True,
                "content": content,
                "file_path": file_path,
                "size": file_size,
                "lines": len(lines)
            }
            
        except Exception as e:
            self.logger.error(f"Error reading file {file_path}: {str(e)}")
            return {"success": False, "error": str(e)}

    def list_directory(self, directory_path, recursive=False):
        """List directory contents"""
        try:
            # Security check
            allowed, message = self._is_path_allowed(directory_path)
            if not allowed:
                return {"success": False, "error": message}
            
            if not os.path.exists(directory_path):
                return {"success": False, "error": f"Directory not found: {directory_path}"}
            
            if not os.path.isdir(directory_path):
                return {"success": False, "error": f"Path is not a directory: {directory_path}"}
            
            items = []
            
            if recursive:
                for root, dirs, files in os.walk(directory_path):
                    # Filter out blocked directories
                    dirs[:] = [d for d in dirs if self._is_path_allowed(os.path.join(root, d))[0]]
                    
                    for name in dirs + files:
                        full_path = os.path.join(root, name)
                        rel_path = os.path.relpath(full_path, directory_path)
                        
                        try:
                            stat = os.stat(full_path)
                            items.append({
                                "name": name,
                                "path": rel_path,
                                "type": "directory" if os.path.isdir(full_path) else "file",
                                "size": stat.st_size if os.path.isfile(full_path) else None,
                                "modified": stat.st_mtime
                            })
                        except (OSError, IOError):
                            continue
            else:
                for item in os.listdir(directory_path):
                    item_path = os.path.join(directory_path, item)
                    
                    # Security check for each item
                    if not self._is_path_allowed(item_path)[0]:
                        continue
                    
                    try:
                        stat = os.stat(item_path)
                        items.append({
                            "name": item,
                            "path": item,
                            "type": "directory" if os.path.isdir(item_path) else "file",
                            "size": stat.st_size if os.path.isfile(item_path) else None,
                            "modified": stat.st_mtime
                        })
                    except (OSError, IOError):
                        continue
            
            return {
                "success": True,
                "directory": directory_path,
                "items": sorted(items, key=lambda x: (x["type"], x["name"])),
                "count": len(items)
            }
            
        except Exception as e:
            self.logger.error(f"Error listing directory {directory_path}: {str(e)}")
            return {"success": False, "error": str(e)}

    def delete_file(self, file_path):
        """Delete a file with security checks"""
        try:
            # Security check
            allowed, message = self._is_path_allowed(file_path)
            if not allowed:
                return {"success": False, "error": message}
            
            if not os.path.exists(file_path):
                return {"success": False, "error": f"File not found: {file_path}"}
            
            if not os.path.isfile(file_path):
                return {"success": False, "error": f"Path is not a file: {file_path}"}
            
            os.remove(file_path)
            
            return {
                "success": True,
                "message": f"File deleted successfully: {file_path}"
            }
            
        except Exception as e:
            self.logger.error(f"Error deleting file {file_path}: {str(e)}")
            return {"success": False, "error": str(e)}

    def create_file(self, file_path, content):
        """Create a new file with content"""
        try:
            # Security check
            allowed, message = self._is_path_allowed(file_path)
            if not allowed:
                return {"success": False, "error": message}
            
            # Create directory if it doesn't exist
            directory = os.path.dirname(file_path)
            if directory and not os.path.exists(directory):
                os.makedirs(directory, exist_ok=True)
            
            # Check if file already exists
            if os.path.exists(file_path):
                return {"success": False, "error": f"File already exists: {file_path}"}
            
            # Write content
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return {
                "success": True,
                "message": f"File created successfully: {file_path}",
                "size": len(content.encode('utf-8'))
            }
            
        except Exception as e:
            self.logger.error(f"Error creating file {file_path}: {str(e)}")
            return {"success": False, "error": str(e)} 