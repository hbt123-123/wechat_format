import json
import pandas as pd
from datetime import datetime

# 读取JSON文件
def read_chat_history(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data

# 统计每天的消息数量并找出最高的10天
def process_top_10_days(chat_data):
    # 提取每条消息的时间戳
    dates = []
    for message in chat_data:
        time_str = message['time']
        # 解析时间戳，格式为 "2024-11-12 23:55:23"
        date = datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S').date()
        dates.append(date)
    
    # 创建日期DataFrame
    df = pd.DataFrame({'date': dates})
    
    # 按日期统计消息数量
    daily_stats = df.groupby('date').size().reset_index()
    daily_stats.columns = ['日期', '消息数量']
    
    # 按消息数量降序排序，取前10名
    top_10_stats = daily_stats.sort_values('消息数量', ascending=False).head(10).reset_index(drop=True)
    
    # 添加排名列
    top_10_stats.insert(0, '排名', range(1, 11))
    
    return top_10_stats

# 将结果写入Excel文件
def write_to_excel(top_10_data, output_file):
    # 创建一个ExcelWriter对象，使用mode='a'追加模式
    with pd.ExcelWriter(output_file, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
        # 将数据写入"聊天数最高10日表"工作表
        top_10_data.to_excel(writer, sheet_name='聊天数最高10日表', index=False)
        
        # 获取工作表对象，设置列宽
        worksheet = writer.sheets['聊天数最高10日表']
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
    top_10_stats = process_top_10_days(chat_data)
    
    # 写入Excel
    write_to_excel(top_10_stats, output_file)
    
    print("统计完成，结果已保存到 project.xlsx 文件。")
    print("\n聊天数最高10日统计：")
    print(top_10_stats)

if __name__ == "__main__":
    main()
