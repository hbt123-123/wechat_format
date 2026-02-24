import json
import pandas as pd
from datetime import datetime
import jieba
from collections import Counter
import re
import calendar
import sys
import os
from openai import OpenAI
from openai import RateLimitError
import time

def read_chat_history(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data

def format_chat_json(input_file, output_file):
    try:
        with open(input_file, "r", encoding="utf-8") as f:
            messages = json.load(f)
        
        optimized_messages = []
        
        for msg in messages:
            time_str = msg.get("time", "")
            formatted_time = ""
            if time_str:
                try:
                    dt = datetime.fromisoformat(time_str.replace("Z", "+00:00"))
                    formatted_time = dt.strftime("%Y-%m-%d %H:%M:%S")
                except ValueError:
                    formatted_time = time_str
            
            is_self = msg.get("isSelf", False)
            sender_name = msg.get("senderName", "")
            
            if is_self:
                formatted_sender = "自己"
            else:
                formatted_sender = sender_name if sender_name else "对方"
            
            msg_type = msg.get("type", 0)
            msg_content = ""
            
            if msg_type == 1:
                msg_content = msg.get("content", "")
            elif msg_type == 3:
                msg_content = "[photo]"
            elif msg_type == 34:
                msg_content = "[voice]"
            elif msg_type == 43:
                msg_content = "[video]"
            elif msg_type == 47:
                msg_content = "[emoji]"
            elif msg_type == 49:
                contents = msg.get("contents", {})
                if contents:
                    if "quote" in contents:
                        quoted_content = contents["quote"].get("content", "")
                        msg_content = f"[引用]: {quoted_content}"
                    elif "forward" in contents:
                        msg_content = "[转发消息]"
                    else:
                        msg_content = "[系统消息]"
                else:
                    msg_content = "[系统消息]"
            elif msg_type in [50, 11000]:
                msg_content = "[语音电话]"
            elif msg_type == 10000:
                msg_content = "[撤回消息]"
            else:
                msg_content = "[其他消息]"
            
            optimized_msg = {
                "time": formatted_time,
                "sender": formatted_sender,
                "message": msg_content
            }
            optimized_messages.append(optimized_msg)
        
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(optimized_messages, f, ensure_ascii=False, indent=2)
        
        print(f"格式化完成，已保存到 {output_file}")
        return True
        
    except Exception as e:
        print(f"格式化失败: {e}")
        return False

def process_voice_calls(chat_data):
    voice_call_records = []
    
    for message in chat_data:
        msg = message['message']
        if msg == '[语音电话]':
            time_str = message['time']
            sender = message['sender']
            datetime_obj = datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S')
            
            voice_call_records.append({
                '日期': datetime_obj.date(),
                '时间': datetime_obj.time(),
                '发送者': sender,
                '完整时间': time_str
            })
    
    df = pd.DataFrame(voice_call_records)
    
    if not df.empty:
        df = df.sort_values('完整时间').reset_index(drop=True)
        df.insert(0, '序号', range(1, len(df) + 1))
    
    return df

def extract_text_messages(chat_data):
    special_messages = [
        '[photo]', '[voice]', '[video]', '[emoji]', '[引用]',
        '[转发消息]', '[语音电话]', '[撤回消息]', '[其他消息]', '[系统消息]'
    ]
    
    text_messages = []
    for message in chat_data:
        msg = message['message']
        if msg not in special_messages and not msg.startswith('[引用]'):
            text_messages.append(msg)
    
    return text_messages

def process_word_frequency(text_messages):
    stop_words = {
        '的', '了', '是', '在', '我', '你', '他', '她', '它', '我们', '你们', '他们',
        '这', '那', '这个', '那个', '就', '都', '也', '还', '又', '再', '很', '非常',
        '啊', '吧', '呢', '吗', '哦', '嗯', '哈', '嘿', '呀', '啦', '嘛', '呗',
        '不', '没', '别', '不要', '不是', '没有', '好', '对', '行', '可以', '知道',
        '什么', '怎么', '为什么', '哪里', '谁', '哪个', '多少', '几', '时候',
        '去', '来', '到', '从', '向', '往', '给', '为', '把', '被', '让',
        '说', '想', '看', '做', '要', '会', '能', '可以', '应该', '需要', '想要',
        '个', '次', '天', '年', '月', '日', '时', '分', '秒', '点', '些', '种',
        '一个', '两个', '三个', '几个', '很多', '一些', '所有', '全部', '每个',
        '因为', '所以', '但是', '不过', '虽然', '可是', '然后', '接着', '最后',
        '或者', '还是', '如果', '要是', '只要', '只有', '无论', '不管', '即使',
        '感觉', '觉得', '认为', '以为', '知道', '明白', '理解', '清楚', '记得',
        '现在', '以前', '以后', '刚才', '马上', '立刻', '很快', '已经', '还是',
        '真的', '确实', '当然', '肯定', '一定', '必须', '应该', '可能', '也许',
        '这样', '那样', '怎么样', '如何', '什么', '哪里', '谁', '为什么',
        '哈哈', '嘿嘿', '呵呵', '嘻嘻', '哎呀', '嗯嗯', '好的', '行吧', '可以啊',
        '吗', '呢', '吧', '啊', '哦', '呀', '啦', '嘛', '呗', '嗯', '哈', '嘿'
    }
    
    all_text = ' '.join(text_messages)
    words = jieba.lcut(all_text)
    
    filtered_words = []
    for word in words:
        if (len(word) > 1 and 
            word not in stop_words and 
            not word.isdigit() and 
            not re.match(r'^[^\w\u4e00-\u9fa5]+$', word)):
            filtered_words.append(word)
    
    word_counts = Counter(filtered_words)
    top_50 = word_counts.most_common(50)
    
    df = pd.DataFrame(top_50, columns=['词语', '出现次数'])
    df.insert(0, '排名', range(1, 51))
    
    return df

def process_top_10_days(chat_data):
    dates = []
    for message in chat_data:
        time_str = message['time']
        date = datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S').date()
        dates.append(date)
    
    df = pd.DataFrame({'date': dates})
    daily_stats = df.groupby('date').size().reset_index()
    daily_stats.columns = ['日期', '消息数量']
    
    top_10_stats = daily_stats.sort_values('消息数量', ascending=False).head(10).reset_index(drop=True)
    top_10_stats.insert(0, '排名', range(1, 11))
    
    return top_10_stats

def process_hourly_trend(chat_data):
    dates = []
    for message in chat_data:
        time_str = message['time']
        date = datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S')
        dates.append(date)
    
    df = pd.DataFrame({'datetime': dates})
    df['hour'] = df['datetime'].dt.hour
    
    hourly_stats = df.groupby('hour').size().reset_index()
    hourly_stats.columns = ['hour', 'count']
    
    all_hours = pd.DataFrame({'hour': range(24)})
    hourly_stats = all_hours.merge(hourly_stats, on='hour', how='left').fillna(0)
    hourly_stats.columns = ['小时', '消息数量']
    hourly_stats['消息数量'] = hourly_stats['消息数量'].astype(int)
    
    return hourly_stats

def process_weekly_trend(chat_data):
    dates = []
    for message in chat_data:
        time_str = message['time']
        date = datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S')
        dates.append(date)
    
    df = pd.DataFrame({'datetime': dates})
    df['weekday'] = df['datetime'].dt.weekday
    
    weekly_stats = df.groupby('weekday').size().reset_index()
    weekly_stats.columns = ['weekday', 'count']
    
    all_weekdays = pd.DataFrame({'weekday': range(7)})
    weekly_stats = all_weekdays.merge(weekly_stats, on='weekday', how='left').fillna(0)
    weekly_stats.columns = ['星期', '消息数量']
    weekly_stats['消息数量'] = weekly_stats['消息数量'].astype(int)
    
    weekday_names = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
    weekly_stats['星期'] = weekly_stats['星期'].map(lambda x: weekday_names[x])
    
    return weekly_stats

def process_monthly_trend(chat_data):
    dates = []
    for message in chat_data:
        time_str = message['time']
        date = datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S')
        dates.append(date)
    
    df = pd.DataFrame({'datetime': dates})
    df['day'] = df['datetime'].dt.day
    
    monthly_stats = df.groupby('day').size().reset_index()
    monthly_stats.columns = ['day', 'count']
    
    all_days = pd.DataFrame({'day': range(1, 31)})
    monthly_stats = all_days.merge(monthly_stats, on='day', how='left').fillna(0)
    monthly_stats.columns = ['日期', '消息数量']
    monthly_stats['消息数量'] = monthly_stats['消息数量'].astype(int)
    
    return monthly_stats

def process_weekly_data(chat_data):
    dates = []
    for message in chat_data:
        time_str = message['time']
        date = datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S')
        dates.append(date)
    
    df = pd.DataFrame({'datetime': dates})
    df['date'] = df['datetime'].dt.date
    df['year_week'] = df['datetime'].dt.strftime('%Y-%W')
    df['week_start'] = df['datetime'].dt.to_period('W').apply(lambda x: x.start_time.date())
    df['week_end'] = df['datetime'].dt.to_period('W').apply(lambda x: x.end_time.date())
    
    weekly_stats = df.groupby(['year_week', 'week_start', 'week_end']).size().reset_index()
    weekly_stats.columns = ['年-周', '周开始日期', '周结束日期', '消息数量']
    weekly_stats = weekly_stats.sort_values('年-周').reset_index(drop=True)
    
    return weekly_stats

def process_monthly_data(chat_data):
    dates = []
    for message in chat_data:
        time_str = message['time']
        date = datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S')
        dates.append(date)
    
    df = pd.DataFrame({'datetime': dates})
    df['year_month'] = df['datetime'].dt.strftime('%Y-%m')
    
    monthly_stats = df.groupby('year_month').size().reset_index()
    monthly_stats.columns = ['年月', '消息数量']
    monthly_stats = monthly_stats.sort_values('年月').reset_index(drop=True)
    
    return monthly_stats

def process_monthly_percentage(chat_data):
    dates = []
    for message in chat_data:
        time_str = message['time']
        date = datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S').date()
        dates.append(date)
    
    df = pd.DataFrame({'date': dates})
    df['date'] = pd.to_datetime(df['date'])
    
    df['year_month'] = df['date'].dt.strftime('%Y-%m')
    monthly_chat_days = df.groupby('year_month')['date'].nunique().reset_index()
    monthly_chat_days.columns = ['年月', '聊天天数']
    
    monthly_chat_days['总天数'] = monthly_chat_days['年月'].apply(lambda x: 
        calendar.monthrange(int(x.split('-')[0]), int(x.split('-')[1]))[1])
    
    monthly_chat_days['占比'] = monthly_chat_days['聊天天数'] / monthly_chat_days['总天数']
    monthly_chat_days['占比(%)'] = monthly_chat_days['占比'].apply(lambda x: f"{x:.2%}")
    
    return monthly_chat_days

def chat_to_dataframe(chat_data):
    df = pd.DataFrame(chat_data)
    df['datetime'] = pd.to_datetime(df['time'])
    df['date'] = df['datetime'].dt.date
    df['week'] = df['datetime'].dt.to_period('W')
    return df

def group_by_week(df):
    weekly_groups = df.groupby('week')
    
    weekly_chats = []
    for week, group in weekly_groups:
        week_chats = group.sort_values('datetime')
        start_date = week_chats['datetime'].min().strftime('%Y-%m-%d %H:%M:%S')
        end_date = week_chats['datetime'].max().strftime('%Y-%m-%d %H:%M:%S')
        
        weekly_chats.append({
            'week': week,
            'start_time': start_date,
            'end_time': end_date,
            'messages': week_chats.to_dict('records'),
            'count': len(week_chats)
        })
    
    weekly_chats.sort(key=lambda x: x['week'].start_time)
    return weekly_chats

def format_chat_for_ai(messages):
    formatted = []
    for msg in messages:
        sender = msg['sender']
        content = msg['message']
        time_str = msg['time']
        formatted.append(f"[{time_str}] {sender}: {content}")
    return '\n'.join(formatted)

def analyze_emotion(chat_text, week_info, client, model_list):
    current_model_index = 0
    
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

    for attempt in range(3):
        model = model_list[current_model_index]
        current_model_index = (current_model_index + 1) % len(model_list)
        
        print(f"\n正在使用模型：{model} (尝试 {attempt+1}/3)")
        
        try:
            extra_body = {"enable_thinking": True}
            
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {'role': 'system', 'content': '你是一个专业的情感分析专家，请分析聊天记录的情绪变化。'},
                    {'role': 'user', 'content': prompt}
                ],
                stream=True,
                extra_body=extra_body
            )
            
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
            time.sleep(2)
        except Exception as e:
            print(f"\n调用模型 {model} 时发生错误，正在切换到下一个模型...")
            print(f"错误信息：{e}")
            time.sleep(2)
    
    return "[分析失败：所有模型都无法使用]"

def emotion_analysis(input_file, api_base_url, api_key, output_file):
    client = OpenAI(base_url=api_base_url, api_key=api_key)
    
    model_list = [
        'deepseek-ai/DeepSeek-V3.2',
        'deepseek-ai/DeepSeek-R1-Distill-Llama-70B',
        'Qwen/Qwen3-Next-80B-A3B-Instruct'
    ]
    
    print("正在读取聊天记录...")
    chat_data = read_chat_history(input_file)
    
    df = chat_to_dataframe(chat_data)
    weekly_chats = group_by_week(df)
    
    print(f"\n共分为 {len(weekly_chats)} 个周批次\n")
    
    all_results = []
    if os.path.exists(output_file):
        try:
            with open(output_file, 'r', encoding='utf-8') as f:
                all_results = json.load(f)
            print(f"已加载 {len(all_results)} 条现有结果")
        except:
            print("加载现有结果失败，将重新开始")
            all_results = []
    
    for i in range(len(weekly_chats)):
        week_chat = weekly_chats[i]
        
        print(f"\n{'='*60}")
        print(f"批次 {i+1}/{len(weekly_chats)}")
        print(f"时间范围：{week_chat['start_time']} 到 {week_chat['end_time']}")
        print(f"消息数量：{week_chat['count']} 条")
        print(f"{'='*60}")
        
        batch_exists = False
        for result in all_results:
            if result['batch'] == i+1:
                batch_exists = True
                print(f"\n该批次已处理过，跳过...")
                break
        
        if batch_exists:
            continue
        
        chat_text = format_chat_for_ai(week_chat['messages'])
        emotion_result = analyze_emotion(chat_text, week_chat, client, model_list)
        
        result = {
            'batch': i+1,
            'week': str(week_chat['week']),
            'start_time': week_chat['start_time'],
            'end_time': week_chat['end_time'],
            'message_count': week_chat['count'],
            'emotion_analysis': emotion_result
        }
        all_results.append(result)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_results, f, ensure_ascii=False, indent=2)
        print(f"\n结果已保存到 {output_file}")
        
        if i < len(weekly_chats) - 1:
            print(f"\n将在 10 秒后自动处理下一批次...")
            for j in range(10, 0, -1):
                print(f"{j}...", end='', flush=True)
                time.sleep(1)
            print("\n")
    
    print(f"\n=== 聊天情绪分析完成 ===")
    print(f"共处理 {len(all_results)} 个周批次")
    print(f"结果文件：{output_file}")

def run_all_stats(input_file, output_file):
    print("正在读取聊天记录...")
    chat_data = read_chat_history(input_file)
    
    print("正在执行统计分析...")
    
    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
        voice_call_data = process_voice_calls(chat_data)
        if not voice_call_data.empty:
            voice_call_data.to_excel(writer, sheet_name='语音电话表', index=False)
            print(f"  - 语音电话统计: {len(voice_call_data)} 条记录")
        
        text_messages = extract_text_messages(chat_data)
        word_stats = process_word_frequency(text_messages)
        word_stats.to_excel(writer, sheet_name='常用词表', index=False)
        print(f"  - 常用词语统计: TOP50")
        
        top_10_stats = process_top_10_days(chat_data)
        top_10_stats.to_excel(writer, sheet_name='聊天数最高10日表', index=False)
        print(f"  - 聊天数最高10日统计完成")
        
        hourly_stats = process_hourly_trend(chat_data)
        hourly_stats.to_excel(writer, sheet_name='24小时趋势表', index=False)
        
        weekly_stats = process_weekly_trend(chat_data)
        weekly_stats.to_excel(writer, sheet_name='周趋势表', index=False)
        
        monthly_stats = process_monthly_trend(chat_data)
        monthly_stats.to_excel(writer, sheet_name='月趋势表', index=False)
        print(f"  - 24小时/周/月趋势统计完成")
        
        weekly_data = process_weekly_data(chat_data)
        weekly_data.to_excel(writer, sheet_name='周消息数量表', index=False)
        
        monthly_data = process_monthly_data(chat_data)
        monthly_data.to_excel(writer, sheet_name='月消息数量表', index=False)
        print(f"  - 周/月消息频次统计完成")
        
        monthly_percentage = process_monthly_percentage(chat_data)
        monthly_percentage.to_excel(writer, sheet_name='消息月占比', index=False)
        print(f"  - 消息月占比统计完成")
        
        for sheet_name in writer.sheets:
            worksheet = writer.sheets[sheet_name]
            for column_cells in worksheet.columns:
                length = max(len(str(cell.value)) for cell in column_cells)
                worksheet.column_dimensions[column_cells[0].column_letter].width = length + 2
    
    print(f"\n所有统计完成！结果已保存到 {output_file}")

def show_menu():
    print("\n" + "="*60)
    print("         微信聊天记录分析工具")
    print("="*60)
    print("1. 格式化聊天记录JSON文件")
    print("2. 统计分析（语音电话、常用词、消息趋势等）")
    print("3. 情绪分析（需要API配置）")
    print("4. 查看情绪分析结果")
    print("5. 退出")
    print("="*60)

def main():
    print("欢迎使用微信聊天记录分析工具！")
    
    json_file = input("请输入要分析的聊天记录JSON文件路径: ").strip()
    
    if not json_file:
        print("文件路径不能为空！")
        return
    
    base_name = json_file.rsplit('.', 1)[0] if '.' in json_file else json_file
    format_file = f"{base_name}_format.json"
    excel_file = f"{base_name}_analysis.xlsx"
    emotion_file = f"{base_name}_emotion.json"
    
    while True:
        show_menu()
        choice = input("请选择功能（1-5）: ").strip()
        
        if choice == '1':
            print(f"\n正在格式化 {json_file}...")
            format_chat_json(json_file, format_file)
            
        elif choice == '2':
            if not os.path.exists(format_file):
                print(f"\n格式化文件不存在，请先执行功能1进行格式化！")
                continue
            print(f"\n正在对 {format_file} 进行统计分析...")
            run_all_stats(format_file, excel_file)
            
        elif choice == '3':
            if not os.path.exists(format_file):
                print(f"\n格式化文件不存在，请先执行功能1进行格式化！")
                continue
            
            print("\n=== API 配置 ===")
            api_base = input("请输入API Base URL（如 https://api-inference.modelscope.cn/v1）: ").strip()
            api_key = input("请输入API Key: ").strip()
            
            if not api_base or not api_key:
                print("API配置不能为空！")
                continue
            
            print(f"\n正在对 {format_file} 进行情绪分析...")
            emotion_analysis(format_file, api_base, api_key, emotion_file)
            
        elif choice == '4':
            if not os.path.exists(emotion_file):
                print(f"\n情绪分析结果文件不存在，请先执行功能3！")
                continue
            
            try:
                with open(emotion_file, 'r', encoding='utf-8') as f:
                    results = json.load(f)
                
                print(f"\n共读取到 {len(results)} 个批次的分析结果")
                print("="*80)
                print("聊天情绪分析结果")
                print("="*80)
                
                for i, result in enumerate(results):
                    print("\n" + "="*80)
                    print(f"批次 {result['batch']}（共 {len(results)} 个批次，当前第 {i+1} 个）")
                    print(f"时间范围：{result['start_time']} 到 {result['end_time']}")
                    print(f"消息数量：{result['message_count']} 条")
                    print("="*80)
                    print("\n情绪分析结果：")
                    print(result['emotion_analysis'])
                    print("\n" + "="*80)
                    
                    if i < len(results) - 1:
                        user_input = input("\n按回车键继续查看下一个批次，输入 'q' 退出：")
                        if user_input.lower() == 'q':
                            print("\n已退出查看")
                            break
                else:
                    print("\n\n所有批次已查看完毕")
                    
            except Exception as e:
                print(f"读取情绪分析结果失败: {e}")
            
        elif choice == '5':
            print("\n感谢使用，再见！")
            break
        else:
            print("\n无效选择，请重新输入！")

if __name__ == "__main__":
    main()
