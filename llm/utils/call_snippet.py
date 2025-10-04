SYSTEM_PROMPT = '''
Merge all changes from the <update> snippet into the <code> below.
- Preserve the code's structure, order, comments, and indentation exactly.
- Output only the updated code, enclosed within <updated-code> and </updated-code> tags.
- Do not include any additional text, explanations, placeholders, ellipses, or code fences.

<code>{original_code}</code>

<update>{update_snippet}</update>

The code is any type of code and the edit is in the form of:

// ... existing code ...
FIRST_EDIT
// ... existing code ...
SECOND_EDIT
// ... existing code ...
THIRD_EDIT
// ... existing code ...

The merged code must be exact with no room for any errors. Make sure all whitespaces are preserved correctly. A small typo in code will cause it to fail to compile or error out, leading to poor user experience.
Provide the complete updated code.
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

<update>
{edit_snippet}
</update>"""
    
    response = ollama.chat(model='modelscope.cn/QuantFactory/FastApply-1.5B-v1.0-GGUF:latest', stream=False, messages=[
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
            'content': '<updated-code>',
        },
    ])
    
    content = response['message']['content']
    if '<updated-code>' in content and '</updated-code>' in content:
        start = content.find('<updated-code>') + len('<updated-code>')
        end = content.find('</updated-code>')
        edited_code = content[start:end]
    elif '</updated-code>' in content:
        edited_code = content.split('</updated-code>')[0]
    else:
        edited_code = content

    # print(edited_code)
    return edited_code

# # Example usage
# original_code = "def hello():\n    print('Hello, World!')"
# edit_snippet = "// ... existing code ...\n    print('Hello, World!')\n    print('Hello, Universe!')\n// ... existing code ..."
# result = apply_code_edit(original_code, edit_snippet)

