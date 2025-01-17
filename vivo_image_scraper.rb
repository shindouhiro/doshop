require 'nokogiri'
require 'httparty'
require 'open-uri'
require 'fileutils'
require 'roo'
require 'json'
require 'selenium-webdriver'

class VivoImageScraper
  def initialize(excel_path)
    @excel_path = excel_path
    @output_dir = "product_images"
    FileUtils.mkdir_p(@output_dir)
    
    # 初始化 Selenium WebDriver
    @driver = Selenium::WebDriver.for :chrome
    puts "\n初始化爬虫:"
    puts "- Excel文件路径: #{@excel_path}"
    puts "- 输出目录: #{@output_dir}"
  end

  def read_products_from_excel
    puts "\n读取Excel文件..."
    workbook = Roo::Spreadsheet.open(@excel_path)
    sheet = workbook.sheet(0)
    puts "- 总行数: #{sheet.last_row}"
    
    # 跳过表头，从第二行开始读取
    products = []
    2.upto(sheet.last_row) do |row|
      product_name = sheet.cell(row, 1).to_s.strip
      products << product_name unless product_name.empty?
    end
    products
  end

  def scrape_images
    products = read_products_from_excel
    puts "\n从Excel中读取到 #{products.length} 个产品"
    puts "产品列表: #{products.join(', ')}"

    products.each_with_index do |product_name, index|
      puts "\n" + "="*50
      puts "处理第 #{index + 1}/#{products.length} 个产品: #{product_name}"
      scrape_product_images(product_name)
      puts "="*50
    end
  end

  private

  def scrape_product_images(product_name)
    begin
      # 访问搜索页面
      puts "\n访问搜索页面..."
      @driver.get("https://search.zol.com.cn/s/")
      
      # 等待搜索框加载
      search_input = @driver.find_element(id: 'keyword')
      search_button = @driver.find_element(class: 'search-btn')
      
      # 输入搜索关键词
      puts "输入搜索关键词: #{product_name}"
      search_input.clear
      search_input.send_keys(product_name)
      
      # 点击搜索按钮
      puts "点击搜索按钮..."
      search_button.click
      
      # 等待搜索结果加载
      sleep 2  # 可以改用显式等待
      
      # 获取页面内容
      search_doc = Nokogiri::HTML(@driver.page_source)
      
      # 获取第一个搜索结果的链接
      product_link = search_doc.css('.pro-intro a').first&.[]('href')
      puts(product_link,"product_link")
      if product_link
        product_url = product_link.start_with?('//') ? "https:#{product_link}" : product_link
        puts "找到产品页面链接: #{product_url}"
        
        # 访问产品详情页
        puts "\n访问产品详情页..."
        product_response = HTTParty.get(product_url, headers: {
          'User-Agent' => 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
          'Accept' => 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
          'Accept-Language' => 'zh-CN,zh;q=0.9,en;q=0.8'
        })
        
        puts "产品页面响应状态码: #{product_response.code}"
        
        if product_response.code == 200
          product_doc = Nokogiri::HTML(product_response.body)
          puts "\n解析产品页面..."
          
          # 获取大图链接
          image_urls = product_doc.css('.big-pic-box img').map { |img| 
            img['src']&.start_with?('//') ? "https:#{img['src']}" : img['src']
          }.compact.uniq
          
          puts "找到图片URL数量: #{image_urls.length}"
          puts "图片URL列表:"
          image_urls.each_with_index do |url, idx|
            puts "  #{idx + 1}. #{url}"
          end

          if image_urls.empty?
            puts "\n警告: 未找到任何图片URL"
            puts "页面内容预览:"
            puts product_response.body[0..500] + "..."
          else
            download_images(image_urls, product_name)
          end
        else
          puts "访问产品页面失败: #{product_response.code}"
        end
      else
        puts "未找到产品页面链接"
        puts "搜索页面内容预览:"
        puts search_response.body[0..500] + "..."
      end
    rescue => e
      puts "处理产品 #{product_name} 时发生错误:"
      puts "- 错误类型: #{e.class}"
      puts "- 错误信息: #{e.message}"
      puts "- 错误堆栈:"
      puts e.backtrace[0..5]
    end
  end

  def download_images(urls, product_name)
    puts "\n开始下载图片..."
    urls.each_with_index do |url, index|
      begin
        next if url.nil? || url.empty?
        
        extension = File.extname(url).empty? ? '.jpg' : File.extname(url)
        safe_product_name = product_name.gsub(/[^0-9A-Za-z\-]/, '_')
        filename = File.join(@output_dir, "#{safe_product_name}_#{index + 1}#{extension}")
        
        puts "\n下载第 #{index + 1} 张图片:"
        puts "- 源URL: #{url}"
        puts "- 保存为: #{filename}"
        
        URI.open(url) do |image|
          File.open(filename, 'wb') do |file|
            file.write(image.read)
          end
        end
        
        puts "✓ 成功下载图片: #{filename}"
        puts "- 文件大小: #{File.size(filename)} 字节"
      rescue => e
        puts "× 下载图片失败 #{url}:"
        puts "- 错误类型: #{e.class}"
        puts "- 错误信息: #{e.message}"
      end
    end
  end

  # 确保关闭浏览器
  def close
    @driver.quit if @driver
  end
end

# 修改运行代码以确保正确关闭浏览器
if ARGV.empty?
  puts "请提供Excel文件路径，例如: ruby vivo_image_scraper.rb products.xlsx"
else
  scraper = VivoImageScraper.new(ARGV[0])
  begin
    scraper.scrape_images
  ensure
    scraper.close
  end
end 