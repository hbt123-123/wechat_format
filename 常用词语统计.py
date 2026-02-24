import json
import pandas as pd
import jieba
from collections import Counter
import re

# 读取JSON文件
def read_chat_history(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data

# 过滤特殊消息和提取文本
def extract_text_messages(chat_data):
    # 定义需要过滤的特殊消息类型
    special_messages = [
        '[photo]',
        '[voice]',
        '[video]',
        '[emoji]',
        '[引用]',
        '[转发消息]',
        '[语音电话]',
        '[撤回消息]',
        '[其他消息]',
        '[系统消息]'
    ]
    
    text_messages = []
    for message in chat_data:
        msg = message['message']
        # 过滤掉特殊消息
        if msg not in special_messages and not msg.startswith('[引用]'):
            text_messages.append(msg)
    
    return text_messages

# 分词并统计词频
def process_word_frequency(text_messages):
    # 定义停用词（常见的无意义词语）
    stop_words = {
        '的', '了', '是', '在', '我', '你', '他', '她', '它', '我们', '你们', '他们',
        '这', '那', '这个', '那个', '就', '都', '也', '还', '又', '再', '很', '非常',
        '啊', '吧', '呢', '吗', '哦', '嗯', '哈', '嘿', '呀', '啦', '嘛', '呗',
        '不', '没', '别', '不要', '不是', '没有', '好', '对', '行', '可以', '知道',
        '什么', '怎么', '为什么', '哪里', '谁', '哪个', '多少', '几', '时候',
        '去', '来', '到', '在', '从', '向', '往', '给', '为', '把', '被', '让',
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
    
    # 合并所有文本
    all_text = ' '.join(text_messages)
    
    # 使用jieba分词
    words = jieba.lcut(all_text)
    
    # 过滤停用词和单字（保留有意义的词语）
    filtered_words = []
    for word in words:
        # 过滤条件：长度大于1，不是停用词，不是纯数字，不是纯符号
        if (len(word) > 1 and 
            word not in stop_words and 
            not word.isdigit() and 
            not re.match(r'^[^\w\u4e00-\u9fa5]+$', word)):
            filtered_words.append(word)
    
    # 统计词频
    word_counts = Counter(filtered_words)
    
    # 获取TOP50
    top_50 = word_counts.most_common(50)
    
    # 转换为DataFrame
    df = pd.DataFrame(top_50, columns=['词语', '出现次数'])
    df.insert(0, '排名', range(1, 51))
    
    return df

# 将结果写入Excel文件
def write_to_excel(word_data, output_file):
    # 创建一个ExcelWriter对象，使用mode='a'追加模式
    with pd.ExcelWriter(output_file, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
        # 将数据写入"常用词表"工作表
        word_data.to_excel(writer, sheet_name='常用词表', index=False)
        
        # 获取工作表对象，设置列宽
        worksheet = writer.sheets['常用词表']
        for column_cells in worksheet.columns:
            length = max(len(str(cell.value)) for cell in column_cells)
            worksheet.column_dimensions[column_cells[0].column_letter].width = length + 2

def main():
    # 输入文件路径
    input_file = 'your_chat_format.json'  # 请替换为您的格式化后的JSON文件
    output_file = 'analysis_result.xlsx'  # 输出Excel文件
    
    # 读取聊天记录
    chat_data = read_chat_history(input_file)
    
    # 提取文本消息
    text_messages = extract_text_messages(chat_data)
    
    # 处理词频统计
    word_stats = process_word_frequency(text_messages)
    
    # 写入Excel
    write_to_excel(word_stats, output_file)
    
    print("统计完成，结果已保存到 project.xlsx 文件。")
    print(f"\n共处理 {len(text_messages)} 条文本消息")
    print("\n常用词语TOP50统计：")
    print(word_stats)

if __name__ == "__main__":
    main()
