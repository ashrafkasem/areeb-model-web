#!/usr/bin/env python3
"""
Areeb Model Web - Cursor Tools Proxy for Qwen3
"""

import os
import sys
import json
import logging
from flask import Flask, request, Response, jsonify
import requests
from utils.config_loader import ConfigLoader
from utils.logger import setup_logging
from tools.file_operations import FileOperations
from tools.terminal_operations import TerminalOperations
from tools.search_operations import SearchOperations
from tools.edit_operations import EditOperations

class AreebModelProxy:
    def __init__(self, config_path="config.yaml"):
        self.config = ConfigLoader(config_path)
        self.logger = setup_logging(self.config)
        
        # Initialize tool handlers
        self.file_ops = FileOperations(self.config, self.logger)
        self.terminal_ops = TerminalOperations(self.config, self.logger)
        self.search_ops = SearchOperations(self.config, self.logger)
        self.edit_ops = EditOperations(self.config, self.logger)
        
        self.app = Flask(__name__)
        self.setup_routes()
        
    def setup_routes(self):
        """Setup Flask routes"""
        
        @self.app.route('/v1/chat/completions', methods=['POST'])
        def chat_completions():
            return self.handle_chat_completion()
            
        @self.app.route('/v1/models', methods=['GET'])
        def list_models():
            return self.handle_list_models()
            
        @self.app.route('/health', methods=['GET'])
        def health_check():
            return jsonify({"status": "healthy", "service": "areeb-model-web"})
            
        @self.app.route('/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
        def proxy_other(path):
            return self.proxy_request(path)

    def get_available_tools(self):
        """Define all available tools for Cursor"""
        tools = []
        
        if self.config.get('tools.enable_file_operations', True):
            tools.extend([
                {
                    "type": "function",
                    "function": {
                        "name": "read_file",
                        "description": "Read the contents of a file within your codebase",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "file_path": {
                                    "type": "string", 
                                    "description": "Path to the file to read"
                                }
                            },
                            "required": ["file_path"]
                        }
                    }
                },
                {
                    "type": "function",
                    "function": {
                        "name": "list_directory",
                        "description": "Read the structure of a directory without reading file contents",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "directory_path": {
                                    "type": "string",
                                    "description": "Path to the directory to list"
                                },
                                "recursive": {
                                    "type": "boolean",
                                    "description": "Whether to list recursively",
                                    "default": False
                                }
                            },
                            "required": ["directory_path"]
                        }
                    }
                },
                {
                    "type": "function",
                    "function": {
                        "name": "delete_file",
                        "description": "Delete a file from the filesystem",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "file_path": {
                                    "type": "string",
                                    "description": "Path to the file to delete"
                                }
                            },
                            "required": ["file_path"]
                        }
                    }
                }
            ])
        
        if self.config.get('tools.enable_terminal', True):
            tools.append({
                "type": "function",
                "function": {
                    "name": "terminal_command",
                    "description": "Execute terminal commands and monitor output",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "command": {
                                "type": "string",
                                "description": "Command to execute in terminal"
                            },
                            "working_directory": {
                                "type": "string",
                                "description": "Working directory for command execution",
                                "default": "."
                            }
                        },
                        "required": ["command"]
                    }
                }
            })
        
        if self.config.get('tools.enable_edit_operations', True):
            tools.extend([
                {
                    "type": "function",
                    "function": {
                        "name": "edit_file",
                        "description": "Edit and apply changes to files",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "file_path": {
                                    "type": "string",
                                    "description": "Path to the file to edit"
                                },
                                "content": {
                                    "type": "string",
                                    "description": "New content for the file"
                                },
                                "start_line": {
                                    "type": "integer",
                                    "description": "Starting line number for partial edit"
                                },
                                "end_line": {
                                    "type": "integer", 
                                    "description": "Ending line number for partial edit"
                                }
                            },
                            "required": ["file_path", "content"]
                        }
                    }
                },
                {
                    "type": "function",
                    "function": {
                        "name": "create_file",
                        "description": "Create a new file with specified content",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "file_path": {
                                    "type": "string",
                                    "description": "Path where the new file should be created"
                                },
                                "content": {
                                    "type": "string",
                                    "description": "Content for the new file"
                                }
                            },
                            "required": ["file_path", "content"]
                        }
                    }
                }
            ])
            
        # Search tools
        tools.extend([
            {
                "type": "function",
                "function": {
                    "name": "search_files",
                    "description": "Find files by name using fuzzy matching",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "pattern": {
                                "type": "string",
                                "description": "Search pattern for file names"
                            },
                            "directory": {
                                "type": "string",
                                "description": "Directory to search in",
                                "default": "."
                            }
                        },
                        "required": ["pattern"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "grep_search",
                    "description": "Search for exact keywords or patterns within files",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "pattern": {
                                "type": "string",
                                "description": "Pattern to search for"
                            },
                            "directory": {
                                "type": "string",
                                "description": "Directory to search in",
                                "default": "."
                            },
                            "file_pattern": {
                                "type": "string",
                                "description": "File pattern to limit search",
                                "default": "*"
                            }
                        },
                        "required": ["pattern"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "codebase_search",
                    "description": "Perform semantic searches within indexed codebase",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Semantic search query"
                            },
                            "file_types": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "File types to include in search"
                            }
                        },
                        "required": ["query"]
                    }
                }
            }
        ])
        
        return tools

    def execute_tool_call(self, tool_name, arguments):
        """Execute a tool call and return the result"""
        try:
            self.logger.info(f"Executing tool: {tool_name} with args: {arguments}")
            
            # File operations
            if tool_name == "read_file":
                return self.file_ops.read_file(arguments.get("file_path"))
            elif tool_name == "list_directory":
                return self.file_ops.list_directory(
                    arguments.get("directory_path"),
                    arguments.get("recursive", False)
                )
            elif tool_name == "delete_file":
                return self.file_ops.delete_file(arguments.get("file_path"))
            elif tool_name == "create_file":
                return self.file_ops.create_file(
                    arguments.get("file_path"),
                    arguments.get("content")
                )
            
            # Edit operations
            elif tool_name == "edit_file":
                return self.edit_ops.edit_file(
                    arguments.get("file_path"),
                    arguments.get("content"),
                    arguments.get("start_line"),
                    arguments.get("end_line")
                )
            
            # Terminal operations
            elif tool_name == "terminal_command":
                return self.terminal_ops.execute_command(
                    arguments.get("command"),
                    arguments.get("working_directory", ".")
                )
            
            # Search operations
            elif tool_name == "search_files":
                return self.search_ops.search_files(
                    arguments.get("pattern"),
                    arguments.get("directory", ".")
                )
            elif tool_name == "grep_search":
                return self.search_ops.grep_search(
                    arguments.get("pattern"),
                    arguments.get("directory", "."),
                    arguments.get("file_pattern", "*")
                )
            elif tool_name == "codebase_search":
                return self.search_ops.codebase_search(
                    arguments.get("query"),
                    arguments.get("file_types", [])
                )
            
            else:
                return {
                    "success": False,
                    "error": f"Unknown tool: {tool_name}"
                }
                
        except Exception as e:
            self.logger.error(f"Error executing tool {tool_name}: {str(e)}")
            return {
                "success": False,
                "error": f"Tool execution failed: {str(e)}"
            }

    def handle_chat_completion(self):
        """Handle chat completion requests"""
        try:
            data = request.get_json()
            
            # Log the incoming request
            self.logger.info(f"Chat completion request: {json.dumps(data, indent=2)}")
            
            # Add tools if not present
            if 'tools' not in data or not data['tools']:
                data['tools'] = self.get_available_tools()
                self.logger.info(f"Added {len(data['tools'])} tools to request")
            
            # Forward to Qwen3 model
            model_endpoint = f"{self.config.get('model.endpoint')}/v1/chat/completions"
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f"Bearer {self.config.get('model.api_key')}"
            }
            
            response = requests.post(
                model_endpoint,
                json=data,
                headers=headers,
                timeout=self.config.get('model.timeout', 300)
            )
            
            self.logger.info(f"Model response status: {response.status_code}")
            
            if response.status_code == 200:
                response_data = response.json()
                
                # Check if model wants to call tools
                if 'choices' in response_data and response_data['choices']:
                    choice = response_data['choices'][0]
                    message = choice.get('message', {})
                    
                    if 'tool_calls' in message and message['tool_calls']:
                        # Execute tool calls
                        tool_results = []
                        for tool_call in message['tool_calls']:
                            function = tool_call.get('function', {})
                            tool_name = function.get('name')
                            arguments = json.loads(function.get('arguments', '{}'))
                            
                            result = self.execute_tool_call(tool_name, arguments)
                            tool_results.append({
                                "tool_call_id": tool_call.get('id'),
                                "role": "tool",
                                "name": tool_name,
                                "content": json.dumps(result)
                            })
                        
                        # Add tool results to conversation and get final response
                        data['messages'].append(message)
                        data['messages'].extend(tool_results)
                        
                        # Remove tools from follow-up request to avoid recursion
                        follow_up_data = data.copy()
                        follow_up_data.pop('tools', None)
                        
                        final_response = requests.post(
                            model_endpoint,
                            json=follow_up_data,
                            headers=headers,
                            timeout=self.config.get('model.timeout', 300)
                        )
                        
                        return Response(
                            final_response.content,
                            final_response.status_code,
                            final_response.headers.items()
                        )
            
            return Response(
                response.content,
                response.status_code,
                response.headers.items()
            )
            
        except Exception as e:
            self.logger.error(f"Error in chat completion: {str(e)}")
            return jsonify({
                "error": {
                    "message": f"Proxy error: {str(e)}",
                    "type": "proxy_error"
                }
            }), 500

    def handle_list_models(self):
        """Handle model listing requests"""
        try:
            model_endpoint = f"{self.config.get('model.endpoint')}/v1/models"
            headers = {
                'Authorization': f"Bearer {self.config.get('model.api_key')}"
            }
            
            response = requests.get(model_endpoint, headers=headers)
            return Response(
                response.content,
                response.status_code,
                response.headers.items()
            )
        except Exception as e:
            self.logger.error(f"Error listing models: {str(e)}")
            return jsonify({
                "object": "list",
                "data": [{
                    "id": self.config.get('model.model_name'),
                    "object": "model",
                    "created": 1234567890,
                    "owned_by": "areeb-model-web"
                }]
            })

    def proxy_request(self, path):
        """Proxy other requests to the model endpoint"""
        try:
            url = f"{self.config.get('model.endpoint')}/{path}"
            headers = dict(request.headers)
            headers['Authorization'] = f"Bearer {self.config.get('model.api_key')}"
            
            response = requests.request(
                method=request.method,
                url=url,
                headers=headers,
                data=request.get_data(),
                params=request.args
            )
            
            return Response(
                response.content,
                response.status_code,
                response.headers.items()
            )
        except Exception as e:
            self.logger.error(f"Error proxying request to {path}: {str(e)}")
            return jsonify({"error": str(e)}), 500

    def run(self):
        """Start the proxy server"""
        host = self.config.get('server.host', '0.0.0.0')
        port = self.config.get('server.port', 8001)
        debug = self.config.get('server.debug', False)
        
        self.logger.info(f"Starting Areeb Model Web proxy on {host}:{port}")
        self.app.run(host=host, port=port, debug=debug)

if __name__ == '__main__':
    proxy = AreebModelProxy()
    proxy.run() 