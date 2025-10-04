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

def apply_code_edit(original_code, edit_snippet):
    """
    Apply an edit to original code using the Osmosis model.
    
    Args:
        original_code (str): The original code to be edited
        edit_snippet (str): The edit to be applied
    
    Returns:
        str: The response from the model
    """
    import ollama
    
    user_prompt = f"""<code>
{original_code}
</code>

<edit>
{edit_snippet}
</edit>"""
    
    response = ollama.chat(
        model='Osmosis/Osmosis-Apply-1.7B',
        stream=False,
        messages=[
            {
                'role': 'system',
                'content': SYSTEM_PROMPT,
            },
            {
                'role': 'user',
                'content': user_prompt,
            },
        ],
    )
    
    content = response['message']['content'].strip()
    if content.startswith('<code>'):
        content = content[len('<code>'):]
    if content.endswith('</code>'):
        content = content[:-len('</code>')]
    return content.strip()

# Example usage
# original_code = "def hello():\n    print('Hello, World!')"
# edit_snippet = "// ... existing code ...\n    print('Hello, World!')\n    print('Hello, Universe!')\n// ... existing code ..."
# result = apply_code_edit(original_code, edit_snippet)
# print(result)