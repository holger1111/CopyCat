import json
with open(r'c:\Users\holge_l\AppData\Roaming\Code\User\workspaceStorage\6a24d7c821246d3c48b87e4bde8cb5f0\GitHub.copilot-chat\transcripts\3483d230-0232-4979-bee3-965a90d39f4d.jsonl', encoding='utf-8') as f:
    lines = f.readlines()
# Find messages where I presented new ideas to the user
for i, line in enumerate(lines):
    try:
        obj = json.loads(line)
        if obj.get('type') != 'assistant.message':
            continue
        content = obj.get('data', {}).get('content', '')
        if 'VS Code Extension' in content and 'Exclude' in content and len(content) > 500:
            print(f'Line {i} (content len={len(content)}):')
            print(content[:4000])
            print('===')
    except:
        pass



