import json
import pandas as pd
import calendar
from datetime import datetime

# 读取JSON文件
def read_chat_history(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data

# 处理聊天记录，统计每月聊天天数
def process_chat_data(chat_data):
    # 提取每条消息的时间戳
    dates = []
    for message in chat_data:
        time_str = message['time']
        # 解析时间戳，格式为 "2024-11-12 23:55:23"
        date = datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S').date()
        dates.append(date)
    
    # 创建日期DataFrame
    df = pd.DataFrame({'date': dates})
    # 确保date列是datetime64类型
    df['date'] = pd.to_datetime(df['date'])
    
    # 按年月分组，统计每月聊天的天数
    df['year_month'] = df['date'].dt.strftime('%Y-%m')
    monthly_chat_days = df.groupby('year_month')['date'].nunique().reset_index()
    monthly_chat_days.columns = ['年月', '聊天天数']
    
    # 计算每月总天数
    monthly_chat_days['总天数'] = monthly_chat_days['年月'].apply(lambda x: 
        calendar.monthrange(int(x.split('-')[0]), int(x.split('-')[1]))[1])
    
    # 计算占比
    monthly_chat_days['占比'] = monthly_chat_days['聊天天数'] / monthly_chat_days['总天数']
    monthly_chat_days['占比(%)'] = monthly_chat_days['占比'].apply(lambda x: f"{x:.2%}")
    
    return monthly_chat_days

# 将结果写入Excel文件
def write_to_excel(data, output_file):
    # 创建一个ExcelWriter对象
    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
        # 将数据写入"消息月占比"工作表
        data.to_excel(writer, sheet_name='消息月占比', index=False)
        
        # 获取工作表对象，设置列宽
        worksheet = writer.sheets['消息月占比']
        for column_cells in worksheet.columns:
            length = max(len(str(cell.value)) for cell in column_cells)
            worksheet.column_dimensions[column_cells[0].column_letter].width = length + 2

def main():
    # 输入文件路径
    input_file = 'your_chat_format.json'  # 请替换为您的格式化后的JSON文件
    output_file = 'analysis_result.xlsx'  # 输出Excel文件
    
    # 读取聊天记录
    chat_data = read_chat_history(input_file)
    
    # 处理数据
    monthly_stats = process_chat_data(chat_data)
    
    # 写入Excel
    write_to_excel(monthly_stats, output_file)
    
    print("统计完成，结果已保存到 project.xlsx 文件中的 '消息月占比' 工作表。")
    print("\n统计结果预览：")
    print(monthly_stats)

if __name__ == "__main__":
    main()
