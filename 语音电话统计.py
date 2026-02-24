import json
import pandas as pd
from datetime import datetime

# 读取JSON文件
def read_chat_history(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data

# 统计语音电话出现的时间
def process_voice_calls(chat_data):
    voice_call_records = []
    
    for message in chat_data:
        msg = message['message']
        # 检查是否为语音电话消息
        if msg == '[语音电话]':
            time_str = message['time']
            sender = message['sender']
            # 解析时间戳，格式为 "2024-11-12 23:55:23"
            datetime_obj = datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S')
            
            voice_call_records.append({
                '日期': datetime_obj.date(),
                '时间': datetime_obj.time(),
                '发送者': sender,
                '完整时间': time_str
            })
    
    # 转换为DataFrame
    df = pd.DataFrame(voice_call_records)
    
    # 按时间排序
    if not df.empty:
        df = df.sort_values('完整时间').reset_index(drop=True)
        df.insert(0, '序号', range(1, len(df) + 1))
    
    return df

# 将结果写入Excel文件
def write_to_excel(voice_call_data, output_file):
    # 创建一个ExcelWriter对象，使用mode='a'追加模式
    with pd.ExcelWriter(output_file, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
        # 将数据写入"语音电话表"工作表
        voice_call_data.to_excel(writer, sheet_name='语音电话表', index=False)
        
        # 获取工作表对象，设置列宽
        worksheet = writer.sheets['语音电话表']
        for column_cells in worksheet.columns:
            length = max(len(str(cell.value)) for cell in column_cells)
            worksheet.column_dimensions[column_cells[0].column_letter].width = length + 2

def main():
    # 输入文件路径
    input_file = 'your_chat_format.json'  # 请替换为您的格式化后的JSON文件
    output_file = 'analysis_result.xlsx'  # 输出Excel文件
    
    # 读取聊天记录
    chat_data = read_chat_history(input_file)
    
    # 处理语音电话数据
    voice_call_stats = process_voice_calls(chat_data)
    
    # 写入Excel
    write_to_excel(voice_call_stats, output_file)
    
    print("统计完成，结果已保存到 project.xlsx 文件。")
    if not voice_call_stats.empty:
        print(f"\n共找到 {len(voice_call_stats)} 次语音电话记录")
        print("\n语音电话统计：")
        print(voice_call_stats)
    else:
        print("\n未找到语音电话记录")

if __name__ == "__main__":
    main()
