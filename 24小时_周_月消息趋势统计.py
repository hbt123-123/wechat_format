import json
import pandas as pd
from datetime import datetime

# 读取JSON文件
def read_chat_history(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data

# 统计24小时趋势
def process_hourly_trend(chat_data):
    # 提取每条消息的时间戳
    dates = []
    for message in chat_data:
        time_str = message['time']
        # 解析时间戳，格式为 "2024-11-12 23:55:23"
        date = datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S')
        dates.append(date)
    
    # 创建日期DataFrame
    df = pd.DataFrame({'datetime': dates})
    df['hour'] = df['datetime'].dt.hour
    
    # 按小时统计消息数量
    hourly_stats = df.groupby('hour').size().reset_index()
    hourly_stats.columns = ['hour', 'count']
    
    # 确保包含所有24小时（0-23）
    all_hours = pd.DataFrame({'hour': range(24)})
    hourly_stats = all_hours.merge(hourly_stats, on='hour', how='left').fillna(0)
    hourly_stats.columns = ['小时', '消息数量']
    hourly_stats['消息数量'] = hourly_stats['消息数量'].astype(int)
    
    return hourly_stats

# 统计周趋势（周一到周日）
def process_weekly_trend(chat_data):
    # 提取每条消息的时间戳
    dates = []
    for message in chat_data:
        time_str = message['time']
        # 解析时间戳，格式为 "2024-11-12 23:55:23"
        date = datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S')
        dates.append(date)
    
    # 创建日期DataFrame
    df = pd.DataFrame({'datetime': dates})
    # 获取星期几（0=周一，6=周日）
    df['weekday'] = df['datetime'].dt.weekday
    
    # 按星期统计消息数量
    weekly_stats = df.groupby('weekday').size().reset_index()
    weekly_stats.columns = ['weekday', 'count']
    
    # 确保包含所有7天（0-6）
    all_weekdays = pd.DataFrame({'weekday': range(7)})
    weekly_stats = all_weekdays.merge(weekly_stats, on='weekday', how='left').fillna(0)
    weekly_stats.columns = ['星期', '消息数量']
    weekly_stats['消息数量'] = weekly_stats['消息数量'].astype(int)
    
    # 将数字转换为星期名称
    weekday_names = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
    weekly_stats['星期'] = weekly_stats['星期'].map(lambda x: weekday_names[x])
    
    return weekly_stats

# 统计月趋势（1-30日）
def process_monthly_trend(chat_data):
    # 提取每条消息的时间戳
    dates = []
    for message in chat_data:
        time_str = message['time']
        # 解析时间戳，格式为 "2024-11-12 23:55:23"
        date = datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S')
        dates.append(date)
    
    # 创建日期DataFrame
    df = pd.DataFrame({'datetime': dates})
    df['day'] = df['datetime'].dt.day
    
    # 按日期统计消息数量
    monthly_stats = df.groupby('day').size().reset_index()
    monthly_stats.columns = ['day', 'count']
    
    # 确保包含1-30日
    all_days = pd.DataFrame({'day': range(1, 31)})
    monthly_stats = all_days.merge(monthly_stats, on='day', how='left').fillna(0)
    monthly_stats.columns = ['日期', '消息数量']
    monthly_stats['消息数量'] = monthly_stats['消息数量'].astype(int)
    
    return monthly_stats

# 将结果写入Excel文件
def write_to_excel(hourly_data, weekly_data, monthly_data, output_file):
    # 创建一个ExcelWriter对象，使用mode='a'追加模式
    with pd.ExcelWriter(output_file, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
        # 将24小时数据写入"24小时趋势表"工作表
        hourly_data.to_excel(writer, sheet_name='24小时趋势表', index=False)
        
        # 将周数据写入"周趋势表"工作表
        weekly_data.to_excel(writer, sheet_name='周趋势表', index=False)
        
        # 将月数据写入"月趋势表"工作表
        monthly_data.to_excel(writer, sheet_name='月趋势表', index=False)
        
        # 获取工作表对象，设置列宽
        for sheet_name in ['24小时趋势表', '周趋势表', '月趋势表']:
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
    hourly_stats = process_hourly_trend(chat_data)
    weekly_stats = process_weekly_trend(chat_data)
    monthly_stats = process_monthly_trend(chat_data)
    
    # 写入Excel
    write_to_excel(hourly_stats, weekly_stats, monthly_stats, output_file)
    
    print("统计完成，结果已保存到 project.xlsx 文件。")
    print("\n24小时趋势统计预览：")
    print(hourly_stats)
    print("\n周趋势统计预览：")
    print(weekly_stats)
    print("\n月趋势统计预览：")
    print(monthly_stats)

if __name__ == "__main__":
    main()
