"""
Search operations for file and content searching
"""

import os
import glob
import re
import subprocess
from pathlib import Path

class SearchOperations:
    def __init__(self, config, logger):
        self.config = config
        self.logger = logger
        self.max_results = 100
        self.max_output_lines = config.get('security.max_output_lines', 1000)

    def search_files(self, pattern, directory="."):
        """Search for files by name using fuzzy matching"""
        try:
            if not os.path.exists(directory):
                return {"success": False, "error": f"Directory not found: {directory}"}
            
            matches = []
            search_pattern = f"**/*{pattern}*"
            
            # Use glob for pattern matching
            for file_path in glob.glob(search_pattern, root_dir=directory, recursive=True):
                full_path = os.path.join(directory, file_path)
                if os.path.isfile(full_path):
                    try:
                        stat = os.stat(full_path)
                        matches.append({
                            "path": file_path,
                            "full_path": full_path,
                            "size": stat.st_size,
                            "modified": stat.st_mtime
                        })
                    except (OSError, IOError):
                        continue
                
                if len(matches) >= self.max_results:
                    break
            
            # Sort by relevance (exact matches first, then by path length)
            matches.sort(key=lambda x: (
                pattern.lower() not in os.path.basename(x["path"]).lower(),
                len(x["path"]),
                x["path"].lower()
            ))
            
            return {
                "success": True,
                "pattern": pattern,
                "directory": directory,
                "matches": matches[:self.max_results],
                "total_found": len(matches),
                "truncated": len(matches) >= self.max_results
            }
            
        except Exception as e:
            self.logger.error(f"Error searching files with pattern '{pattern}': {str(e)}")
            return {"success": False, "error": str(e)}

    def grep_search(self, pattern, directory=".", file_pattern="*"):
        """Search for patterns within files using grep-like functionality"""
        try:
            if not os.path.exists(directory):
                return {"success": False, "error": f"Directory not found: {directory}"}
            
            matches = []
            compiled_pattern = re.compile(pattern, re.IGNORECASE)
            
            # Find files matching the file pattern
            search_files = glob.glob(
                os.path.join(directory, "**", file_pattern), 
                recursive=True
            )
            
            for file_path in search_files:
                if not os.path.isfile(file_path):
                    continue
                
                try:
                    # Skip binary files
                    with open(file_path, 'rb') as f:
                        chunk = f.read(1024)
                        if b'\0' in chunk:
                            continue
                    
                    # Search in file
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        for line_num, line in enumerate(f, 1):
                            if compiled_pattern.search(line):
                                matches.append({
                                    "file": os.path.relpath(file_path, directory),
                                    "line_number": line_num,
                                    "line_content": line.strip(),
                                    "match_positions": [
                                        (m.start(), m.end()) 
                                        for m in compiled_pattern.finditer(line)
                                    ]
                                })
                                
                                if len(matches) >= self.max_output_lines:
                                    break
                    
                except (UnicodeDecodeError, IOError):
                    continue
                
                if len(matches) >= self.max_output_lines:
                    break
            
            return {
                "success": True,
                "pattern": pattern,
                "directory": directory,
                "file_pattern": file_pattern,
                "matches": matches,
                "total_found": len(matches),
                "truncated": len(matches) >= self.max_output_lines
            }
            
        except Exception as e:
            self.logger.error(f"Error in grep search for pattern '{pattern}': {str(e)}")
            return {"success": False, "error": str(e)}

    def codebase_search(self, query, file_types=None):
        """Perform semantic search within codebase"""
        try:
            # This is a simplified implementation
            # In a real scenario, you might use tools like ripgrep, ag, or semantic search
            
            if file_types is None:
                file_types = ["*.py", "*.js", "*.ts", "*.java", "*.cpp", "*.c", "*.h"]
            
            all_matches = []
            
            # Search in each file type
            for file_type in file_types:
                matches = self.grep_search(query, ".", file_type)
                if matches["success"]:
                    all_matches.extend(matches["matches"])
            
            # Remove duplicates and sort by relevance
            seen = set()
            unique_matches = []
            for match in all_matches:
                key = (match["file"], match["line_number"])
                if key not in seen:
                    seen.add(key)
                    unique_matches.append(match)
            
            # Sort by file name and line number
            unique_matches.sort(key=lambda x: (x["file"], x["line_number"]))
            
            return {
                "success": True,
                "query": query,
                "file_types": file_types,
                "matches": unique_matches[:self.max_output_lines],
                "total_found": len(unique_matches),
                "truncated": len(unique_matches) >= self.max_output_lines
            }
            
        except Exception as e:
            self.logger.error(f"Error in codebase search for query '{query}': {str(e)}")
            return {"success": False, "error": str(e)}

    def find_definition(self, symbol, file_types=None):
        """Find definition of a symbol in codebase"""
        try:
            if file_types is None:
                file_types = ["*.py", "*.js", "*.ts", "*.java", "*.cpp", "*.c", "*.h"]
            
            # Common definition patterns
            patterns = [
                f"def {symbol}",      # Python function
                f"class {symbol}",    # Python/Java class
                f"function {symbol}", # JavaScript function
                f"{symbol}\\s*=",     # Variable assignment
                f"const {symbol}",    # JavaScript const
                f"let {symbol}",      # JavaScript let
                f"var {symbol}",      # JavaScript var
            ]
            
            all_matches = []
            
            for pattern in patterns:
                for file_type in file_types:
                    matches = self.grep_search(pattern, ".", file_type)
                    if matches["success"]:
                        all_matches.extend(matches["matches"])
            
            # Remove duplicates
            seen = set()
            unique_matches = []
            for match in all_matches:
                key = (match["file"], match["line_number"])
                if key not in seen:
                    seen.add(key)
                    unique_matches.append(match)
            
            return {
                "success": True,
                "symbol": symbol,
                "matches": unique_matches,
                "total_found": len(unique_matches)
            }
            
        except Exception as e:
            self.logger.error(f"Error finding definition for '{symbol}': {str(e)}")
            return {"success": False, "error": str(e)} 