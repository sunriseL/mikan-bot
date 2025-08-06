import json
import os

def load_prompts():
    """从JSON文件加载prompt配置"""
    json_path = os.path.join(os.path.dirname(__file__), 'prompts.json')
    
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('prompts', {}), data.get('default_key', '小日向美香')
    except FileNotFoundError:
        print(f"Warning: prompts.json not found at {json_path}")
        return {}, '小日向美香'
    except json.JSONDecodeError as e:
        print(f"Error parsing prompts.json: {e}")
        return {}, '小日向美香'

# 加载prompt配置
prompt_map, default_key = load_prompts() 