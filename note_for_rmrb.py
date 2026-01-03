# -*- coding: utf-8 -*-
"""
人民日报PDF智能分析工具
=========================

这个模块提供了对人民日报PDF文件的智能分析功能，能够：
1. 自动提取PDF文本内容
2. 使用大语言模型进行智能分析
3. 生成结构化的分析报告

主要功能：
- 提取人民日报PDF文本
- AI智能分析识别重大事件、评论文章、金句典故、优秀词组
- 生成Markdown格式的分析报告
- 自动按日期命名输出文件

依赖库：
- PyPDF2: PDF文件读取
- OpenAI: 大模型API调用
- datetime: 日期时间处理

作者: 项目维护者
版本: 1.0.0
"""

from datetime import datetime
from openai import OpenAI
from PyPDF2 import PdfReader

# 获取当前日期字符串，用于文件名命名
date_str = datetime.now().strftime('%Y-%m-%d')


def read_pdf(pdf_path):
    """
    从PDF文件中提取文本内容
    
    使用PyPDF2库读取PDF文件，提取所有页面的文本内容，
    各页面文本用单换行符连接。
    
    Args:
        pdf_path (str): PDF文件的完整路径
        
    Returns:
        str: 从PDF中提取的文本内容，各页面之间用换行符分隔
        
    Note:
        这个函数与readpdf.py中的read_pdf函数类似，但连接符不同
        这里使用单换行符，适合后续的AI分析处理
    """
    # 创建PDF阅读器对象并读取文件
    reader = PdfReader(pdf_path)
    
    # 提取所有页面的文本内容
    # page.extract_text() 可能返回None，使用or ""处理空页面
    # 各页面文本用换行符连接，保持一定分隔但比双换行符更紧凑
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def extract_info(content):
    """
    使用大语言模型对文本内容进行智能分析
    
    该函数调用百度AI Studio的ernie-4.5-turbo-vl模型，
    对输入的文本内容进行结构化分析，识别和分类各种信息。
    
    Args:
        content (str): 待分析的文本内容（通常是从PDF提取的报纸内容）
        
    Returns:
        str: AI分析生成的结构化文本内容
        
    Note:
        - 使用流式输出，实时显示AI思考过程和分析结果
        - 分析结果包含重大事件、评论文章、金句典故、优秀词组四个维度
        - 模型配置为低温度(0.2)以确保输出稳定性
    """
    # 初始化OpenAI客户端
    # 注意：API密钥应从环境变量或配置文件获取，避免硬编码
    client = OpenAI(
        # API密钥配置 - 生产环境中应使用环境变量
        api_key="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
        # 百度AI Studio大模型API服务地址
        base_url="https://aistudio.baidu.com/llm/lmapi/v3",
    )

    # 创建聊天完成请求
    chat_completion = client.chat.completions.create(
        # 使用ernie-4.5-turbo-vl模型进行多模态分析
        model="ernie-4.5-turbo-vl",
        
        # 构建对话消息
        messages=[
            {
                "role": "system",
                "content": (
                    "该内容是报纸pdf识别的，内容连续性可能有问题，请你理顺后，"
                    "然后详尽完成下列任务，要详细，尽可能多："
                    "1.报纸中出现的重大事件；"
                    "2.评论员文章；"
                    "3.金句、典故、古语；"
                    "4.优秀词组、新词。"
                ),
            },
            {"role": "user", "content": content},
        ],
        
        # 启用流式输出，实时显示结果
        stream=True,
        
        # 额外的模型参数配置
        extra_body={
            "penalty_score": 1,      # 重复惩罚分数，控制内容重复度
            "enable_thinking": True  # 启用思考模式，提高分析质量
        },
        
        # 模型生成参数
        max_completion_tokens=12000,  # 最大输出token数，确保详细分析
        temperature=0.2,              # 温度参数，低温度保证输出稳定性
        top_p=0.8,                    # 核采样参数
        frequency_penalty=0,          # 频率惩罚，避免重复内容
        presence_penalty=0            # 存在惩罚，鼓励新话题
    )

    # 处理流式输出
    mycontent = ""
    for chunk in chat_completion:
        # 检查是否有有效的选择结果
        if not chunk.choices or len(chunk.choices) == 0:
            continue
            
        choice = chunk.choices[0]
        
        # 处理AI思考过程内容（如果启用思考模式）
        if hasattr(choice.delta, "reasoning_content") and choice.delta.reasoning_content:
            # 实时显示AI的思考过程
            print(choice.delta.reasoning_content, end="", flush=True)
            
        # 处理实际的分析内容
        elif hasattr(choice.delta, "content") and choice.delta.content:
            # 实时显示分析结果
            print(choice.delta.content, end="", flush=True)
            # 累积完整内容用于返回
            mycontent = mycontent + choice.delta.content
            
    # 返回完整的分析结果
    return mycontent


def main():
    """
    主函数 - 程序执行入口
    
    执行完整的PDF分析流程：
    1. 构建当日人民日报PDF文件名
    2. 读取PDF文本内容
    3. 使用AI进行智能分析
    4. 保存分析结果到Markdown文件
    """
    try:
        # 构建当日人民日报PDF文件名 (格式: rmrb_YYYY-MM-DD.pdf)
        rmrb_pdf_file = f"rmrb_{date_str}.pdf"
        print(f"正在读取PDF文件: {rmrb_pdf_file}")
        
        # 提取PDF文本内容
        content = read_pdf(rmrb_pdf_file)
        print(f"PDF文本提取完成，内容长度: {len(content)} 字符")
        
        # 使用AI进行智能分析
        print("\n开始AI分析...")
        markdown_note = extract_info(content)
        print("\nAI分析完成")
        
        # 重新获取日期字符串（确保文件名日期准确）
        current_date = datetime.now().strftime("%Y-%m-%d")
        output_filename = f"人民日报_{current_date}.md"
        
        # 保存分析结果到Markdown文件
        with open(output_filename, "w", encoding="utf-8") as file:
            print(markdown_note, file=file)
            
        print(f"\n分析结果已保存到: {output_filename}")
        
    except FileNotFoundError:
        print(f"错误: 找不到文件 '{rmrb_pdf_file}'")
        print("请确保当日的人民日报PDF文件存在且命名格式正确")
        
    except Exception as e:
        print(f"处理过程中发生错误: {str(e)}")
        print("请检查网络连接和API配置")


if __name__ == "__main__":
    main()
