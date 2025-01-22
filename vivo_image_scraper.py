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
                        # 获取当前页面内容
                        product_doc = BeautifulSoup(self.driver.page_source, 'html.parser')
                        print("产品页面内容:")
                        # 打印断点调试信息
                    
                        print(product_doc.prettify())
                        # 查找参数链接
                        param_link = search_doc.select_one('.nav__list a[href*="/param.shtml"]')
                        if param_link:
                            print("找到参数链接")
                            param_url = param_link.get('href')
                            if param_url:
                                # 确保URL是完整的
                                if not param_url.startswith('http'):
                                    param_url = 'https://detail.zol.com.cn' + param_url
                                print(f"参数页面URL: {param_url}")
                                
                                # 点击链接访问参数页面
                                try:
                                    # 使用更精确的选择器定位参数链接
                                    param_link_element = self.driver.find_element(By.CSS_SELECTOR, '.nav__list.clearfix li a[href*="/param.shtml"]')
                                    param_link_element.click()
                                    time.sleep(2)
                                    
                                    # 获取参数页面内容
                                    param_doc = BeautifulSoup(self.driver.page_source, 'html.parser')
                                    print("参数页面内容:")
                                    print(param_doc.prettify())
                                except Exception as e:
                                    print(f"点击参数链接失败: {str(e)}")
                                    # 如果点击失败,直接访问URL
                                    self.driver.get(param_url)
                                    time.sleep(2)
                                    
                                    # 获取参数页面内容
                                    param_doc = BeautifulSoup(self.driver.page_source, 'html.parser')
                                    print("参数页面内容:")
                                    print(param_doc.prettify())
                            else:
                                print("参数链接href属性为空")
                        else:
                            print("未找到参数链接")
                    except Exception as e:
                        print(f"点击产品链接失败: {str(e)}")
                        # 如果点击失败,直接访问URL
                        self.driver.get(product_url)
                        time.sleep(2)
                else:
                    print("产品链接href属性为空")
            else:
                print("未找到产品链接")
            # 创建产品目录

            # 获取当前页面内容

            # 查找参数链接
            param_link = search_doc.select_one('.nav__list a[href*="/param.shtml"]')
            if param_link:
                print("找到参数链接")
                param_url = param_link.get('href')
                if param_url:
                    # 确保URL是完整的
                    if not param_url.startswith('http'):
                        param_url = 'https://detail.zol.com.cn' + param_url
                    print(f"参数页面URL: {param_url}")
                    
                    # 点击链接访问参数页面
                    try:
                        # 使用更精确的选择器定位参数链接
                        param_link_element = self.driver.find_element(By.CSS_SELECTOR, '.nav__list.clearfix li a[href*="/param.shtml"]')
                        param_link_element.click()
                        time.sleep(2)
                        
                        # 获取参数页面内容
                        param_doc = BeautifulSoup(self.driver.page_source, 'html.parser')
                        print("参数页面内容:")
                        print(param_doc.prettify())
                    except Exception as e:
                        print(f"点击参数链接失败: {str(e)}")
                        # 如果点击失败,直接访问URL
                        self.driver.get(param_url)
                        time.sleep(2)
                        
                        # 获取参数页面内容
                        param_doc = BeautifulSoup(self.driver.page_source, 'html.parser')
                        print("参数页面内容:")
                        print(param_doc.prettify())
                else:
                    print("参数链接href属性为空")
            else:
                print("未找到参数链接")

            # 创建产品目录
            product_dir = os.path.join('images', product_name)
            os.makedirs(product_dir, exist_ok=True)
            print(f"创建目录: {product_dir}")
            
            # 查找所有图片元素
            image_elements = product_doc.select('.big-pic-box img')
            if not image_elements:
                print("未找到图片元素")
                return
                
            print(f"找到 {len(image_elements)} 张图片")
            
            # 下载每张图片
            for i, img in enumerate(image_elements, 1):
                img_url = img.get('src')
                if not img_url:
                    print(f"图片 {i} 没有src属性")
                    continue
                    
                # 确保URL是完整的
                if not img_url.startswith('http'):
                    img_url = 'https:' + img_url
                    
                # 构建保存路径
                img_name = f"{product_name}_{i}.jpg"
                img_path = os.path.join(product_dir, img_name)
                
                try:
                    # 下载图片
                    response = requests.get(img_url, timeout=10)
                    if response.status_code == 200:
                        with open(img_path, 'wb') as f:
                            f.write(response.content)
                        print(f"已保存图片: {img_name}")
                    else:
                        print(f"下载图片 {img_name} 失败: HTTP {response.status_code}")
                except Exception as e:
                    print(f"下载图片 {img_name} 时出错: {str(e)}")
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
