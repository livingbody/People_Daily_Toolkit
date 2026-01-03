# 本项目用于从人民日报网站下载指定日期的PDF版报纸，并将多个版面合并为一个完整的PDF文件
# 作者: livingbody
# pip install requests beautifulsoup4 PyPDF2

import os
import requests
from bs4 import BeautifulSoup
import PyPDF2
import time
from datetime import date, datetime, timedelta
import re


def get_page_count(url):
    """
    获取报纸的总版面数
    
    参数:
        url: 报纸版面目录页的URL
    
    返回值:
        int: 总版面数
    """
    try:
        response = requests.get(url, timeout=10)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 查找所有版面链接
        page_links = soup.find_all('a', href=lambda x: x and 'node_' in x and '.html' in x)
        
        # 提取版面编号并找到最大的编号
        max_page = 0
        for link in page_links:
            match = re.search(r'node_(\d+)\.html', link.get('href'))
            if match:
                page_num = int(match.group(1))
                max_page = max(max_page, page_num)
                
        return max_page
    except Exception as e:
        print(f"获取版面数量失败: {e}")
        return 8  # 默认返回8版


def get_pdf_urls(base_url, date_str):
    """
    获取所有版面的PDF文件URL
    
    参数:
        base_url: 人民日报网站的基础URL
        date_str: 日期字符串，格式为'YYYY-MM-DD'
    
    返回值:
        list: PDF文件URL列表
    """
    year, month, day = date_str.split('-')
    
    # 构建版面目录页URL
    catalog_url = f"{base_url}/rmrb/pc/layout/{year}{month}/{day}/node_01.html"
    
    # 获取版面数量
    page_count = get_page_count(catalog_url)
    print(f"发现 {page_count} 个版面")
    
    pdf_urls = []
    
    # 遍历所有版面
    for i in range(1, page_count + 1):
        # 构建当前版面的URL
        page_url = f"{base_url}/rmrb/pc/layout/{year}{month}/{day}/node_{i:02d}.html"
        
        try:
            response = requests.get(page_url, timeout=10)
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 查找PDF链接
            pdf_link = soup.find('a', href=lambda x: x and x.endswith('.pdf'))
            
            if pdf_link:
                pdf_href = pdf_link.get('href')
                # 如果是相对URL，则构建绝对URL
                if not pdf_href.startswith('http'):
                    if pdf_href.startswith('/'):
                        pdf_href = base_url + pdf_href
                    else:
                        pdf_href = f"{base_url}/rmrb/pc/layout/{year}{month}/{day}/{pdf_href}"
                
                pdf_urls.append(pdf_href)
                print(f"找到版面 {i} 的PDF链接: {pdf_href}")
            else:
                print(f"未找到版面 {i} 的PDF链接")
        except Exception as e:
            print(f"获取版面 {i} 的PDF链接失败: {e}")
            
    return pdf_urls


def download_pdfs(pdf_urls, date_str):
    """
    下载所有PDF文件
    
    参数:
        pdf_urls: PDF文件URL列表
        date_str: 日期字符串，用于命名下载的文件
    
    返回值:
        list: 下载的PDF文件路径列表
    """
    downloaded_files = []
    
    # 创建临时目录存储下载的文件
    temp_dir = f"temp_pdfs_{date_str}"
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)
    
    # 下载每个PDF文件
    for i, pdf_url in enumerate(pdf_urls):
        try:
            # 构建保存的文件名
            file_name = f"{temp_dir}/rmrb_{date_str}_{i+1:02d}.pdf"
            
            # 下载文件
            print(f"开始下载版面 {i+1} 的PDF文件...")
            response = requests.get(pdf_url, timeout=30)
            
            # 保存文件
            with open(file_name, 'wb') as f:
                f.write(response.content)
            
            downloaded_files.append(file_name)
            print(f"版面 {i+1} 的PDF文件下载完成: {file_name}")
            
            # 添加下载间隔，避免请求过于频繁
            time.sleep(1)
        except Exception as e:
            print(f"下载版面 {i+1} 的PDF文件失败: {e}")
    
    return downloaded_files


def merge_pdfs(pdf_files, output_file):
    """
    合并多个PDF文件为一个
    
    参数:
        pdf_files: 要合并的PDF文件路径列表
        output_file: 合并后的输出文件路径
    
    返回值:
        bool: 合并是否成功
    """
    try:
        pdf_writer = PyPDF2.PdfWriter()
        
        # 遍历每个PDF文件
        for pdf_file in pdf_files:
            try:
                pdf_reader = PyPDF2.PdfReader(pdf_file, strict=False)
                
                # 添加每一页到写入器
                for page_num in range(len(pdf_reader.pages)):
                    pdf_writer.add_page(pdf_reader.pages[page_num])
            except Exception as e:
                print(f"读取文件 {pdf_file} 失败: {e}")
        
        # 写入合并后的文件
        with open(output_file, 'wb') as out:
            pdf_writer.write(out)
        
        print(f"PDF文件合并完成: {output_file}")
        return True
    except Exception as e:
        print(f"PDF文件合并失败: {e}")
        return False


def clean_temp_files(temp_files):
    """
    清理临时文件
    
    参数:
        temp_files: 临时文件路径列表
    """
    for file in temp_files:
        try:
            os.remove(file)
        except Exception as e:
            print(f"删除临时文件 {file} 失败: {e}")
    
    # 尝试删除临时目录
    if temp_files:
        temp_dir = os.path.dirname(temp_files[0])
        try:
            os.rmdir(temp_dir)
        except Exception as e:
            print(f"删除临时目录 {temp_dir} 失败: {e}")


def download_rmrb_pdf(date_str=None, base_url="https://paper.people.com.cn"):
    """
    下载指定日期的人民日报PDF并合并
    
    参数:
        date_str: 日期字符串，格式为'YYYY-MM-DD'，默认为当天
        base_url: 人民日报网站的基础URL
    
    返回值:
        str: 合并后的PDF文件路径，如果失败则返回None
    """
    # 如果未指定日期，则使用当天日期
    if date_str is None:
        date_str = datetime.now().strftime('%Y-%m-%d')
    
    print(f"开始下载 {date_str} 的人民日报PDF...")
    
    # 获取所有版面的PDF链接
    pdf_urls = get_pdf_urls(base_url, date_str)
    
    if not pdf_urls:
        print("未找到任何PDF链接，下载失败")
        return None
    
    # 下载PDF文件
    downloaded_files = download_pdfs(pdf_urls, date_str)
    
    if not downloaded_files:
        print("所有PDF文件下载失败")
        return None
    
    # 构建输出文件名
    output_file = f"storage/downloads/rmrb/rmrb_{date_str}.pdf"
    
    # 合并PDF文件
    if merge_pdfs(downloaded_files, output_file):
        # 清理临时文件
        clean_temp_files(downloaded_files)
        print(f"人民日报 {date_str} PDF下载和合并完成！")
        return output_file
    else:
        # 即使合并失败，也清理临时文件
        clean_temp_files(downloaded_files)
        return None


if __name__ == "__main__":
    # 示例用法：下载当天的人民日报PDF
    # 如果需要下载特定日期的报纸，可以传入日期参数，例如：download_rmrb_pdf('2025-09-29')
    # result = download_rmrb_pdf()
        # 如果未指定日期，则使用当天日期
    today=datetime.now()
    download_rmrb_pdf()
    # for i in range(0,300,1):
    #     date_str = (today-timedelta(days=i)).strftime('%Y-%m-%d')
    #     print(f"开始下载 {date_str} 的人民日报PDF...")
    #     result = download_rmrb_pdf(date_str)
    #     if result:
    #         print(f"最终生成的PDF文件: {result}")
    #     else:
    #         print("操作失败")