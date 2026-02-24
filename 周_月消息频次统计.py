import json
import pandas as pd
from datetime import datetime

# 读取JSON文件
def read_chat_history(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data

# 按周统计消息数量
def process_weekly_data(chat_data):
    # 提取每条消息的时间戳
    dates = []
    for message in chat_data:
        time_str = message['time']
        # 解析时间戳，格式为 "2024-11-12 23:55:23"
        date = datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S')
        dates.append(date)
    
    # 创建日期DataFrame
    df = pd.DataFrame({'datetime': dates})
    df['date'] = df['datetime'].dt.date
    df['year_week'] = df['datetime'].dt.strftime('%Y-%W')
    df['week_start'] = df['datetime'].dt.to_period('W').apply(lambda x: x.start_time.date())
    df['week_end'] = df['datetime'].dt.to_period('W').apply(lambda x: x.end_time.date())
    
    # 按周统计消息数量
    weekly_stats = df.groupby(['year_week', 'week_start', 'week_end']).size().reset_index()
    weekly_stats.columns = ['年-周', '周开始日期', '周结束日期', '消息数量']
    
    # 按年-周排序
    weekly_stats = weekly_stats.sort_values('年-周').reset_index(drop=True)
    
    return weekly_stats

# 按月统计消息数量
def process_monthly_data(chat_data):
    # 提取每条消息的时间戳
    dates = []
    for message in chat_data:
        time_str = message['time']
        # 解析时间戳，格式为 "2024-11-12 23:55:23"
        date = datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S')
        dates.append(date)
    
    # 创建日期DataFrame
    df = pd.DataFrame({'datetime': dates})
    df['year_month'] = df['datetime'].dt.strftime('%Y-%m')
    
    # 按月统计消息数量
    monthly_stats = df.groupby('year_month').size().reset_index()
    monthly_stats.columns = ['年月', '消息数量']
    
    # 按年月排序
    monthly_stats = monthly_stats.sort_values('年月').reset_index(drop=True)
    
    return monthly_stats

# 将结果写入Excel文件
def write_to_excel(weekly_data, monthly_data, output_file):
    # 创建一个ExcelWriter对象，使用mode='a'追加模式
    with pd.ExcelWriter(output_file, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
        # 将周数据写入"周消息数量表"工作表
        weekly_data.to_excel(writer, sheet_name='周消息数量表', index=False)
        
        # 将月数据写入"月消息数量表"工作表
        monthly_data.to_excel(writer, sheet_name='月消息数量表', index=False)
        
        # 获取工作表对象，设置列宽
        for sheet_name in ['周消息数量表', '月消息数量表']:
            worksheet = writer.sheets[sheet_name]
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
    weekly_stats = process_weekly_data(chat_data)
    monthly_stats = process_monthly_data(chat_data)
    
    # 写入Excel
    write_to_excel(weekly_stats, monthly_stats, output_file)
    
    print("统计完成，结果已保存到 project.xlsx 文件。")
    print("\n周消息数量统计预览（前10条）：")
    print(weekly_stats.head(10))
    print("\n月消息数量统计预览：")
    print(monthly_stats)

if __name__ == "__main__":
    main()
