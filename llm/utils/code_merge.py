#!/usr/bin/env python3
"""
MCP Server for code snippet editing using the Osmosis model.
"""

import json
import ollama
import os
from typing import Any, Dict, List
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool

app = Server("codemerge")

SYSTEM_PROMPT = \
'''
You are a helpful assistant for a code editor that applies an edit to code to merge them together. That is, you will be given code wrapper in <code> tags and an edit wrapped in <edit> tags, and you will apply the edit to the code.

For example:

<code>
CODE_SNIPPET
</code>

<edit>
EDIT_SNIPPET
</edit>

The code is any type of code and the edit is in the form of:

// ... existing code ...
FIRST_EDIT
// ... existing code ...
SECOND_EDIT
// ... existing code ...
THIRD_EDIT
// ... existing code ...

The merged code must be exact with no room for any errors. Make sure all whitespaces are preserved correctly. A small typo in code will cause it to fail to compile or error out, leading to poor user experience.

Output the code wrapped in <code> tags.
'''

@app.list_tools()
async def list_tools() -> List[Tool]:
    return [
        Tool(
            name="edit_snippet",
            description="Apply an edit to a code snippet using the Osmosis model",
            inputSchema={
                "type": "object",
                "properties": {
                    "original_code": {
                        "type": "string",
                        "description": "The original code to be edited, must be exact match to the original code"
                    },
                    "edit_snippet": {
                        "type": "string",
                        "description": "The edit to be applied, abbreviate original code with // ... existing code ... markers to save space, leave at MOST one or two lines of existing code before and after the edit"
                    },
                    "file_path": {
                        "type": "string",
                        "description": "Optional path to the file to search for original code and replace with output, must be absolute file path"
                    }
                },
                "required": ["original_code", "edit_snippet"]
            }
        )
    ]

@app.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> List[Dict[str, Any]]:
    if name == "edit_snippet":
        return await edit_snippet(arguments)
    else:
        raise ValueError(f"Unknown tool: {name}")

async def edit_snippet(arguments: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Apply an edit to original code using the Osmosis model.
    
    Args:
        arguments: Dictionary containing original_code, edit_snippet, and optional file_path
    
    Returns:
        List with the edited code response and file operation status
    """
    try:
        original_code = arguments["original_code"]
        edit_snippet = arguments["edit_snippet"]
        file_path = arguments.get("file_path")
        
        user_prompt = f"""<code>
{original_code}
</code>


<edit>
{edit_snippet}
</edit>"""
        
        response = ollama.chat(model='Osmosis/Osmosis-Apply-1.7B', stream=False, messages=[
            {
                'role': 'system',
                'content': SYSTEM_PROMPT,
            },
            {
                'role': 'user',
                'content': user_prompt,
            },
            {
                'role': 'assistant',
                'content': '<code>',
            },
        ])
        
        # Extract the code content from the response
        full_response = "<code>" + response['message']['content']
        
        # Extract code between <code> tags
        if '<code>' in full_response and '</code>' in full_response:
            start = full_response.find('<code>') + 6
            end = full_response.find('</code>')
            edited_code = full_response[start:end]
        else:
            edited_code = response['message']['content']
        
        # Handle file operations if file_path is provided
        file_operation_result = ""
        if file_path:
            try:
                if os.path.exists(file_path):
                    # Read the file
                    with open(file_path, 'r', encoding='utf-8') as f:
                        file_content = f.read()
                    
                    # Search for the original code in the file
                    if original_code.strip() in file_content:
                        # Replace the original code with the edited code
                        updated_content = file_content.replace(original_code.strip(), edited_code.strip())
                        
                        # Write the updated content back to the file
                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.write(updated_content)
                        
                        file_operation_result = f"\n\nFile operation: SUCCESS - Original code found and replaced in {file_path}"
                    else:
                        file_operation_result = f"\n\nFile operation: FAILED - Original code not found in {file_path}"
                else:
                    file_operation_result = f"\n\nFile operation: FAILED - File {file_path} does not exist"
            except Exception as file_error:
                file_operation_result = f"\n\nFile operation: FAILED - Error: {str(file_error)}"
        
        return [
            {
                "type": "text",
                "text": file_operation_result
            }
        ]
        
    except Exception as e:
        return [
            {
                "type": "text", 
                "text": f"Error applying edit: {str(e)}"
            }
        ]

async def main():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())