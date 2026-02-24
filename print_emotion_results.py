import json

# 读取情绪分析结果文件
def read_emotion_results(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data

# 打印分析结果
def print_emotion_results(results):
    # 遍历每个分析结果
    for i, result in enumerate(results):
        print("\n" + "="*80)
        print(f"批次 {result['batch']}（共 {len(results)} 个批次，当前第 {i+1} 个）")
        print(f"时间范围：{result['start_time']} 到 {result['end_time']}")
        print(f"消息数量：{result['message_count']} 条")
        print("="*80)
        print("\n情绪分析结果：")
        print(result['emotion_analysis'])
        print("\n" + "="*80)
        
        # 如果不是最后一个批次，等待用户输入
        if i < len(results) - 1:
            user_input = input("\n按回车键继续查看下一个批次，输入 'q' 退出：")
            if user_input.lower() == 'q':
                print("\n已退出查看")
                break
        else:
            print("\n\n所有批次已查看完毕")

# 主程序
def main():
    # 文件路径
    input_file = 'chat_emotion_analysis.json'
    
    try:
        # 读取结果
        results = read_emotion_results(input_file)
        
        print(f"共读取到 {len(results)} 个批次的分析结果")
        print("\n" + "="*80)
        print("聊天情绪分析结果")
        print("="*80)
        
        # 打印结果
        print_emotion_results(results)
        
    except FileNotFoundError:
        print(f"错误：找不到文件 {input_file}")
    except json.JSONDecodeError:
        print(f"错误：文件 {input_file} 不是有效的JSON格式")
    except Exception as e:
        print(f"错误：{e}")

if __name__ == "__main__":
    main()
