import json
from datetime import datetime

# 定义文件路径
input_file = "your_chat.json"  # 请替换为您的聊天记录文件
output_file = "your_chat_format.json"

try:
    # 读取原始JSON文件
    with open(input_file, "r", encoding="utf-8") as f:
        messages = json.load(f)
    
    optimized_messages = []
    
    for msg in messages:
        # 转换时间格式 ISO → YYYY-MM-DD HH:MM:SS
        time_str = msg.get("time", "")
        formatted_time = ""
        if time_str:
            try:
                # 解析ISO时间格式
                dt = datetime.fromisoformat(time_str.replace("Z", "+00:00"))
                # 转换为更易读的格式
                formatted_time = dt.strftime("%Y-%m-%d %H:%M:%S")
            except ValueError:
                formatted_time = time_str
        
        # 规范化发送者名称
        is_self = msg.get("isSelf", False)
        sender_name = msg.get("senderName", "")
        
        if is_self:
            formatted_sender = "自己"
        else:
            # 如果对方没有显示名字，使用默认名称
            formatted_sender = sender_name if sender_name else "对方"  # 可替换为对方的备注名
        
        # 处理消息内容，根据不同类型展示
        msg_type = msg.get("type", 0)
        msg_content = ""
        
        if msg_type == 1:  # 文本消息
            msg_content = msg.get("content", "")
        elif msg_type == 3:  # 图片消息
            msg_content = "[photo]"
        elif msg_type == 34:  # 语音消息
            msg_content = "[voice]"
        elif msg_type == 43:  # 视频消息
            msg_content = "[video]"
        elif msg_type == 47:  # 表情消息
            msg_content = "[emoji]"
        elif msg_type == 49:  # 系统消息，可能包含引用、转发等
            # 检查是否有引用或转发内容
            contents = msg.get("contents", {})
            if contents:
                # 简单处理，展示引用或转发的基本信息
                if "quote" in contents:
                    quoted_content = contents["quote"].get("content", "")
                    msg_content = f"[引用]: {quoted_content}"
                elif "forward" in contents:
                    msg_content = "[转发消息]"
                else:
                    msg_content = "[系统消息]"
            else:
                msg_content = "[系统消息]"
        elif msg_type in [50, 11000]:  # 语音电话
            msg_content = "[语音电话]"
        elif msg_type == 10000:  # 消息撤回
            msg_content = "[撤回消息]"
        else:  # 其他类型
            msg_content = "[其他消息]"
        
        # 创建优化后的消息对象
        optimized_msg = {
            "time": formatted_time,
            "sender": formatted_sender,
            "message": msg_content
        }
        optimized_messages.append(optimized_msg)
    
    # 写入优化后的JSON文件
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(optimized_messages, f, ensure_ascii=False, indent=2)
    
    print(f"优化后的JSON文件已保存到 {output_file}")
    
except json.JSONDecodeError as e:
    print(f"JSON解析错误: {e}")
except IOError as e:
    print(f"文件读写错误: {e}")
except Exception as e:
    print(f"发生未知错误: {e}")
