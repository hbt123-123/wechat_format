import json

# 定义输入输出文件路径
file_path = "your_chat.json"  # 请替换为您的聊天记录文件

try:
    # 读取现有的JSON文件
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    # 格式化JSON数据并写回文件
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"JSON文件已成功格式化并保存到 {file_path}")
    
except json.JSONDecodeError as e:
    print(f"JSON解析错误: {e}")
except IOError as e:
    print(f"文件读写错误: {e}")
except Exception as e:
    print(f"发生未知错误: {e}")