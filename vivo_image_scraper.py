from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
import os
import time
from bs4 import BeautifulSoup
import requests

class VivoImageScraper:
    def __init__(self, excel_path):
        self.excel_path = excel_path
        self.output_dir = "product_images"
        os.makedirs(self.output_dir, exist_ok=True)
        
        # 初始化 Selenium WebDriver
        self.driver = webdriver.Chrome()
        print("\n初始化爬虫:")
        print(f"- Excel文件路径: {self.excel_path}")
        print(f"- 输出目录: {self.output_dir}")

    def scrape_product_images(self, product_name):
        try:
            # 访问搜索页面
            print("\n访问搜索页面...")
            self.driver.get("https://search.zol.com.cn/s/")
            
            # 等待搜索框和按钮加载
            wait = WebDriverWait(self.driver, 10)
            search_input = wait.until(
                EC.presence_of_element_located((By.ID, "keyword"))
            )
            search_button = wait.until(
                EC.presence_of_element_located((By.CLASS_NAME, "search-btn"))
            )
            
            # 输入搜索关键词
            print(f"输入搜索关键词: {product_name}")
            search_input.clear()
            search_input.send_keys(product_name)
            
            # 点击搜索按钮
            print("点击搜索按钮...")
            search_button.click()
            # 打断点
            # 等待搜索结果加载
            time.sleep(2)
            
            # 获取搜索结果页面内容
            search_doc = BeautifulSoup(self.driver.page_source, 'html.parser')
            # 查找产品标签
            product_tab = search_doc.select_one('.search-tab-nav.clearfix a[href*="detail.zol.com.cn"]')
            if product_tab:
                print("找到产品标签")
                # 如果不是当前选中的标签,需要点击切换
                if not 'current' in product_tab.get('class', []):
                    print("切换到产品标签...")
                    product_tab_element = self.driver.find_element(By.CSS_SELECTOR, '.search-tab-nav.clearfix a[href*="detail.zol.com.cn"]')
                    product_tab_element.click()
                    time.sleep(2)
                    # 重新获取页面内容
                    search_doc = BeautifulSoup(self.driver.page_source, 'html.parser')
            else:
                print("未找到产品标签")


            # 查找第一个产品链接
            product_link = search_doc.select_one('.pro-intro h3 a')
            if product_link:
                print("找到产品链接")
                # 获取href属性
                product_url = product_link.get('href')
                if product_url:
                    # 确保URL是完整的
                    if not product_url.startswith('http'):
                        product_url = 'https://detail.zol.com.cn' + product_url
                    print(f"产品URL: {product_url}")
                    
                    # 点击链接访问产品页面
                    try:
                        product_link_element = self.driver.find_element(By.CSS_SELECTOR, '.pro-intro h3 a')
                        product_link_element.click()
                        time.sleep(2)
                    except Exception as e:
                        print(f"点击产品链接失败: {str(e)}")
                        # 如果点击失败,直接访问URL
                        self.driver.get(product_url)
                        time.sleep(2)
                else:
                    print("产品链接href属性为空")
            else:
                print("未找到产品链接")
            # 查找第一个产品链接
            product_link = search_doc.select_one('.search-list .pro-intro h3 a')
            if not product_link:
                print(f"未找到产品 {product_name} 的搜索结果")
                return
            
            # 获取产品链接并访问
            print(product_link,"产品url")
            product_url = product_link.get('href')
            if not product_url.startswith('http'):
                product_url = 'https:' + product_url
            print("访问产品页面: {product_url}")
            self.driver.get(product_url)
            time.sleep(2)
            # 获取产品详情页内容
            product_doc = BeautifulSoup(self.driver.page_source, 'html.parser')
            # 打断点
            
            # 创建产品目录
            safe_product_name = product_name.replace('/', '_').replace('\\', '_')
            product_dir = os.path.join(self.output_dir, safe_product_name)
            os.makedirs(product_dir, exist_ok=True)
            
            # 保存整个product_doc到文本文件
            product_doc_file = os.path.join(product_dir, 'product_doc.txt')
            with open(product_doc_file, 'w', encoding='utf-8') as f:
                f.write(str(product_doc))
            print(f"已保存product_doc到: {product_doc_file}")
            
            # 获取产品内容
            content_items = product_doc.select('.article-content')
            if content_items:
                print("找到产品内容:")
                content_file = os.path.join(product_dir, 'content.txt')
                with open(content_file, 'w', encoding='utf-8') as f:
                    for item in content_items:
                        content = item.get_text(strip=True)
                        print(content)
                        f.write(content + '\n')
                print(f"已保存产品内容到: {content_file}")
            else:
                print("未找到产品内容")
            
            # 获取产品图片
            print("开始下载产品图片...")
            images = product_doc.select('.big-pic-box img')
            for idx, img in enumerate(images):
                img_url = img.get('src')
                if not img_url:
                    continue
                if not img_url.startswith('http'):
                    img_url = 'https:' + img_url
                    
                # 下载图片
                try:
                    response = requests.get(img_url)
                    if response.status_code == 200:
                        img_path = os.path.join(product_dir, f'image_{idx+1}.jpg')
                        with open(img_path, 'wb') as f:
                            f.write(response.content)
                        print(f"已保存图片: {img_path}")
                except Exception as e:
                    print(f"下载图片失败: {img_url}")
                    print(f"错误信息: {str(e)}")
            
            # 获取产品参数
            print("\n获取产品参数...")
            params = {}
            param_items = product_doc.select('.param-list li')
            for item in param_items:
                try:
                    key = item.select_one('.param-name').text.strip()
                    value = item.select_one('.param-value').text.strip()
                    params[key] = value
                except:
                    continue
            
            # 保存参数到文本文件
            params_file = os.path.join(product_dir, 'parameters.txt')
            with open(params_file, 'w', encoding='utf-8') as f:
                for key, value in params.items():
                    f.write(f"{key}: {value}\n")
            print(f"已保存参数到: {params_file}")
            
        except Exception as e:
            print(f"处理产品 {product_name} 时发生错误:")
            print(f"- 错误类型: {type(e).__name__}")
            print(f"- 错误信息: {str(e)}")
            import traceback
            print("- 错误堆栈:")
            print('\n'.join(traceback.format_stack()[:6]))

    def scrape_images(self):
        try:
            # 读取Excel文件
            df = pd.read_excel(self.excel_path)
            
            # 打印列名，帮助调试
            print("\nExcel文件包含以下列:")
            print(df.columns.tolist())
            
            # 使用 "名称" 列而不是 "产品名称" 列
            if '名称' not in df.columns:
                print("\n错误: Excel文件中没有找到'名称'列")
                print("请确保Excel文件中包含'名称'列，或修改以下列名之一:")
                for col in df.columns:
                    print(f"- {col}")
                return
            
            # 遍历每个产品
            for index, row in df.iterrows():
                product_name = row['名称']  # 使用 "名称" 而不是 "产品名称"
                print(f"\n处理第 {index + 1} 个产品: {product_name}")
                self.scrape_product_images(product_name)
                
        except Exception as e:
            print(f"\n读取Excel文件时发生错误: {str(e)}")
            print("请确保:")
            print("1. Excel文件存在且可访问")
            print("2. 文件格式正确（.xlsx或.xls）")
            print("3. 文件未被其他程序占用")
        finally:
            self.close()

    def close(self):
        if hasattr(self, 'driver'):
            self.driver.quit()

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("请提供Excel文件路径，例如: python vivo_image_scraper.py products.xlsx")
    else:
        scraper = VivoImageScraper(sys.argv[1])
        try:
            scraper.scrape_images()
        except KeyboardInterrupt:
            print("\n程序被用户中断")
        finally:
            scraper.close() 