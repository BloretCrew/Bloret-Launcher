import os
import re
import json

qml_dir = "g:/Work/git/Bloret-Launcher/qml"
manifest_zh = "g:/Work/git/Bloret-Launcher/lang/zh-cn.json"
manifest_en = "g:/Work/git/Bloret-Launcher/lang/en-US.json"

qstr_pattern = re.compile(r'qsTr\(\s*"(.*?)"\s*\)')
replacement = r'(Backend ? Backend.tr("\1") : "\1")'

extracted_strings = set()

# Process QML files
for root, dirs, files in os.walk(qml_dir):
    for file in files:
        if file.endswith(".qml"):
            filepath = os.path.join(root, file)
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Find strings
            matches = qstr_pattern.findall(content)
            for match in matches:
                extracted_strings.add(match)
            
            # Replace strings
            new_content = qstr_pattern.sub(replacement, content)
            
            if new_content != content:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                print(f"Updated {filepath}")

# Load existing JSON
def load_json(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading {filepath}: {e}")
        return {"texts": {}}

data_zh = load_json(manifest_zh)
data_en = load_json(manifest_en)

if "texts" not in data_zh: data_zh["texts"] = {}
if "texts" not in data_en: data_en["texts"] = {}

added_zh = 0
added_en = 0

for s in extracted_strings:
    if s not in data_zh["texts"]:
        data_zh["texts"][s] = s  # Default to Chinese for Chinese
        added_zh += 1
    if s not in data_en["texts"]:
        data_en["texts"][s] = s  # Will translate manually later
        added_en += 1

with open(manifest_zh, 'w', encoding='utf-8') as f:
    json.dump(data_zh, f, indent=4, ensure_ascii=False)

with open(manifest_en, 'w', encoding='utf-8') as f:
    json.dump(data_en, f, indent=4, ensure_ascii=False)

print(f"Extracted {len(extracted_strings)} strings.")
print(f"Added {added_zh} to zh-cn.json")
print(f"Added {added_en} to en-US.json")
