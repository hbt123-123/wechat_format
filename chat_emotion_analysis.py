import json
import pandas as pd
from datetime import datetime
from openai import OpenAI
from openai import RateLimitError
import time
import sys
import os

# -------------------
# API 配置
# -------------------
client = OpenAI(
    base_url='https://api-inference.modelscope.cn/v1',
    api_key='YOUR_API_KEY', # 请替换为您的API Key
)

# 设置extra_body for thinking control
extra_body = {
    # enable thinking, set to False to disable
    "enable_thinking": True
}

# 可用模型列表，按优先级排序
MODEL_LIST = [
    'deepseek-ai/DeepSeek-V3.2',
    'deepseek-ai/DeepSeek-R1-Distill-Llama-70B'
    'Qwen/Qwen3-Next-80B-A3B-Instruct',
]

# 当前使用的模型索引
current_model_index = 0

# -------------------
# 函数定义
# -------------------

# 读取聊天记录
def read_chat_history(file_path):
    """读取JSON格式的聊天记录"""
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data

# 将聊天记录转换为DataFrame
def chat_to_dataframe(chat_data):
    """将聊天记录转换为DataFrame，方便后续处理"""
    df = pd.DataFrame(chat_data)
    df['datetime'] = pd.to_datetime(df['time'])
    df['date'] = df['datetime'].dt.date
    df['week'] = df['datetime'].dt.to_period('W')
    return df

# 按周分组，获取每周的聊天记录
def group_by_week(df):
    """按周分组，返回每周的聊天记录"""
    # 按周分组
    weekly_groups = df.groupby('week')
    
    # 准备结果列表
    weekly_chats = []
    for week, group in weekly_groups:
        # 获取该周的所有聊天记录
        week_chats = group.sort_values('datetime')
        # 获取时间范围
        start_date = week_chats['datetime'].min().strftime('%Y-%m-%d %H:%M:%S')
        end_date = week_chats['datetime'].max().strftime('%Y-%m-%d %H:%M:%S')
        
        weekly_chats.append({
            'week': week,
            'start_time': start_date,
            'end_time': end_date,
            'messages': week_chats.to_dict('records'),
            'count': len(week_chats)
        })
    
    # 按时间排序
    weekly_chats.sort(key=lambda x: x['week'].start_time)
    return weekly_chats

# 格式化聊天记录，用于AI分析
def format_chat_for_ai(messages):
    """将聊天记录格式化为AI分析的文本"""
    formatted = []
    for msg in messages:
        sender = msg['sender']
        content = msg['message']
        time_str = msg['time']
        formatted.append(f"[{time_str}] {sender}: {content}")
    return '\n'.join(formatted)

# 获取下一个可用模型
def get_next_model():
    """获取下一个可用模型"""
    global current_model_index
    model = MODEL_LIST[current_model_index]
    current_model_index = (current_model_index + 1) % len(MODEL_LIST)
    return model

# 调用AI API进行情绪分析
def analyze_emotion(chat_text, week_info):
    """调用AI API进行情绪分析，自动切换模型"""
    prompt = f"""你是一个专业的情感分析专家，请分析以下聊天记录的情绪变化，包括：
1. 主要情绪类型（积极、中性、消极）及分布
2. 情绪变化趋势（从开始到结束的情绪变化）
3. 关键情绪事件（引发情绪变化的重要对话）
4. 情绪强度分析（各情绪的强烈程度）
5. 总体情绪总结

请以结构化的方式提供分析结果，方便后续整理。

聊天记录时间范围：{week_info['start_time']} 到 {week_info['end_time']}
聊天记录（共{week_info['count']}条）：
{chat_text}"""

    # 尝试最多3次，每次更换模型
    for attempt in range(3):
        model = get_next_model()
        print(f"\n正在使用模型：{model} (尝试 {attempt+1}/3)")
        
        try:
            response = client.chat.completions.create(
                model=model, # ModelScope Model-Id, required
                messages=[
                    {
                      'role': 'system',
                      'content': '你是一个专业的情感分析专家，请分析聊天记录的情绪变化。'
                    },
                    {
                      'role': 'user',
                      'content': prompt
                    }
                ],
                stream=True,
                extra_body=extra_body
            )
            
            # 处理流式响应
            print("\n=== AI 正在分析，请稍候 ===\n")
            
            thinking_content = ""
            final_answer = ""
            done_thinking = False
            
            for chunk in response:
                if chunk.choices:
                    thinking_chunk = chunk.choices[0].delta.reasoning_content
                    answer_chunk = chunk.choices[0].delta.content
                    if thinking_chunk != '':
                        thinking_content += thinking_chunk
                    elif answer_chunk != '':
                        if not done_thinking:
                            print("=== AI 分析结果 ===\n")
                            done_thinking = True
                        final_answer += answer_chunk
                        print(answer_chunk, end='', flush=True)
            
            print("\n\n=== 分析完成 ===")
            return final_answer
            
        except RateLimitError as e:
            print(f"\n模型 {model} 达到速率限制，正在切换到下一个模型...")
            print(f"错误信息：{e}")
            time.sleep(2)  # 等待2秒后重试
        except Exception as e:
            print(f"\n调用模型 {model} 时发生错误，正在切换到下一个模型...")
            print(f"错误信息：{e}")
            time.sleep(2)  # 等待2秒后重试
    
    # 如果所有模型都失败
    print(f"\n所有模型都无法使用，请稍后重试")
    return "[分析失败：所有模型都无法使用]"

# 保存分析结果
def save_results(results, output_file):
    """保存分析结果到JSON文件"""
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\n当前结果已保存到 {output_file}")

# 显示程序帮助
def show_help():
    """显示程序帮助信息"""
    print("微信聊天情绪分析程序使用说明：")
    print("1. 全部模式：python chat_emotion_analysis.py")
    print("2. 指定批次：python chat_emotion_analysis.py --batch <批次号>")
    print("   例如：python chat_emotion_analysis.py --batch 5")
    print("3. 查看帮助：python chat_emotion_analysis.py --help")
    print("\n程序功能：")
    print("- 按周分批处理聊天记录")
    print("- 自动切换AI模型，避免速率限制")
    print("- 实时保存分析结果到chat_emotion_analysis.json")
    print("- 每批处理后等待10秒自动继续")

# 主程序
def main():
    # 解析命令行参数
    args = sys.argv[1:]
    batch_mode = False
    target_batch = None
    
    if len(args) > 0:
        if args[0] == '--help' or args[0] == '-h':
            show_help()
            return
        elif args[0] == '--batch' and len(args) > 1:
            batch_mode = True
            try:
                target_batch = int(args[1]) - 1  # 转换为索引
            except ValueError:
                print("错误：批次号必须是数字")
                show_help()
                return
        else:
            print("错误：无效的参数")
            show_help()
            return
    
    # 文件路径
    chat_file = 'your_chat_format.json'  # 请替换为您的格式化后的JSON文件
    output_file = 'chat_emotion_analysis.json'
    
    # 读取聊天记录
    print("正在读取聊天记录...")
    chat_data = read_chat_history(chat_file)
    
    # 转换为DataFrame
    df = chat_to_dataframe(chat_data)
    
    # 按周分组
    weekly_chats = group_by_week(df)
    
    print(f"\n共分为 {len(weekly_chats)} 个周批次\n")
    
    # 准备结果列表，如果文件已存在则加载现有结果
    all_results = []
    if os.path.exists(output_file):
        try:
            with open(output_file, 'r', encoding='utf-8') as f:
                all_results = json.load(f)
            print(f"已加载 {len(all_results)} 条现有结果")
        except:
            print("加载现有结果失败，将重新开始")
            all_results = []
    
    # 确定处理范围
    start_index = 0
    end_index = len(weekly_chats)
    
    if batch_mode:
        if 0 <= target_batch < len(weekly_chats):
            start_index = target_batch
            end_index = target_batch + 1
            print(f"\n将只处理第 {target_batch+1} 批次")
        else:
            print(f"错误：批次号超出范围（1-{len(weekly_chats)}")
            return
    
    # 逐个处理每个周批次
    for i in range(start_index, end_index):
        week_chat = weekly_chats[i]
        
        print(f"\n{'='*60}")
        print(f"批次 {i+1}/{len(weekly_chats)}")
        print(f"时间范围：{week_chat['start_time']} 到 {week_chat['end_time']}")
        print(f"消息数量：{week_chat['count']} 条")
        print(f"{'='*60}")
        
        # 检查是否已处理过该批次
        batch_exists = False
        for result in all_results:
            if result['batch'] == i+1:
                batch_exists = True
                print(f"\n该批次已处理过，跳过...")
                break
        
        if batch_exists:
            continue
        
        # 格式化聊天记录
        chat_text = format_chat_for_ai(week_chat['messages'])
        
        # 调用AI分析
        emotion_result = analyze_emotion(chat_text, week_chat)
        
        # 保存结果
        result = {
            'batch': i+1,
            'week': str(week_chat['week']),
            'start_time': week_chat['start_time'],
            'end_time': week_chat['end_time'],
            'message_count': week_chat['count'],
            'emotion_analysis': emotion_result
        }
        all_results.append(result)
        
        # 实时保存结果
        save_results(all_results, output_file)
        
        # 如果不是最后一个批次，等待10秒后继续
        if i < end_index - 1:
            print(f"\n将在 10 秒后自动处理下一批次...")
            for j in range(10, 0, -1):
                print(f"{j}...", end='', flush=True)
                time.sleep(1)
            print("\n")
    
    print(f"\n=== 聊天情绪分析完成 ===")
    print(f"共处理 {len(all_results)} 个周批次")
    print(f"结果文件：{output_file}")

if __name__ == "__main__":
    main()