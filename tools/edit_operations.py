"""
Edit operations for file modification
"""

import os
import shutil
from datetime import datetime

class EditOperations:
    def __init__(self, config, logger):
        self.config = config
        self.logger = logger
        self.auto_apply = config.get('tools.auto_apply_edits', False)
        self.backup_dir = "backups"

    def _create_backup(self, file_path):
        """Create a backup of the file before editing"""
        try:
            if not os.path.exists(file_path):
                return True, None
            
            # Create backup directory
            os.makedirs(self.backup_dir, exist_ok=True)
            
            # Generate backup filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"{os.path.basename(file_path)}.{timestamp}.backup"
            backup_path = os.path.join(self.backup_dir, backup_name)
            
            # Copy file to backup
            shutil.copy2(file_path, backup_path)
            
            return True, backup_path
            
        except Exception as e:
            self.logger.error(f"Error creating backup for {file_path}: {str(e)}")
            return False, str(e)

    def edit_file(self, file_path, content, start_line=None, end_line=None):
        """Edit file with optional line range"""
        try:
            # Security check (reuse from file_operations)
            from .file_operations import FileOperations
            file_ops = FileOperations(self.config, self.logger)
            allowed, message = file_ops._is_path_allowed(file_path)
            if not allowed:
                return {"success": False, "error": message}
            
            # Create backup
            backup_success, backup_path = self._create_backup(file_path)
            if not backup_success:
                return {"success": False, "error": f"Failed to create backup: {backup_path}"}
            
            if start_line is not None and end_line is not None:
                # Partial edit
                if not os.path.exists(file_path):
                    return {"success": False, "error": f"File not found: {file_path}"}
                
                # Read existing content
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                
                # Validate line numbers
                if start_line < 1 or end_line < start_line or start_line > len(lines):
                    return {
                        "success": False, 
                        "error": f"Invalid line range: {start_line}-{end_line} (file has {len(lines)} lines)"
                    }
                
                # Replace lines
                new_content_lines = content.split('\n')
                if not content.endswith('\n'):
                    new_content_lines = [line + '\n' for line in new_content_lines[:-1]] + [new_content_lines[-1]]
                else:
                    new_content_lines = [line + '\n' for line in new_content_lines]
                
                # Adjust for 0-based indexing
                lines[start_line-1:end_line] = new_content_lines
                
                # Write back
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.writelines(lines)
                
                return {
                    "success": True,
                    "message": f"File edited successfully (lines {start_line}-{end_line}): {file_path}",
                    "backup_path": backup_path,
                    "lines_modified": end_line - start_line + 1,
                    "new_lines": len(new_content_lines)
                }
            
            else:
                # Full file replacement
                # Create directory if it doesn't exist
                directory = os.path.dirname(file_path)
                if directory and not os.path.exists(directory):
                    os.makedirs(directory, exist_ok=True)
                
                # Write new content
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                return {
                    "success": True,
                    "message": f"File edited successfully: {file_path}",
                    "backup_path": backup_path,
                    "size": len(content.encode('utf-8')),
                    "lines": len(content.split('\n'))
                }
            
        except Exception as e:
            self.logger.error(f"Error editing file {file_path}: {str(e)}")
            return {"success": False, "error": str(e)} 