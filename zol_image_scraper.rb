require 'nokogiri'
require 'httparty'
require 'open-uri'
require 'fileutils'
require 'roo'

class ZOLImageScraper
  # 构造函数初始化后:
  # 1. 调用 read_products_from_excel 方法读取Excel文件中的产品列表
  # 2. 调用 scrape_all_products 方法开始爬取所有产品图片
  # 3. scrape_all_products 会遍历每个产品调用 scrape_product 方法
  # 4. scrape_product 会调用 scrape_product_page 处理产品详情页
  # 5. 最后通过 download_single_image 下载每张图片
  def initialize(excel_path)
    @excel_path = excel_path
    @output_dir = "product_images"
    FileUtils.mkdir_p(@output_dir)
  end

  def read_products_from_excel
    begin
      workbook = Roo::Spreadsheet.open(@excel_path)
      sheet = workbook.sheet(0)
      # 跳过表头，从第二行开始读取
      products = []
      2.upto(sheet.last_row) do |row|
        product_name = sheet.cell(row, 1).to_s.strip
        products << product_name unless product_name.empty?
      end
      puts "从Excel中读取到 #{products.length} 个产品"
      products
    rescue => e
      puts "读取Excel文件失败: #{e.message}"
      []
    end
  end

  def scrape_all_products
    products = read_products_from_excel
    puts "产品列表: #{products.join(', ')}"
    products.each_with_index do |product_name, index|
      puts "\n处理第 #{index + 1}/#{products.length} 个产品: #{product_name}"
      scrape_product(product_name)
    end
  end

  def scrape_product(product_name)
    begin
      # ZOL搜索页面
      search_url = "https://detail.zol.com.cn/search/index.html?keyword=#{URI.encode_www_form_component(product_name)}"
      response = HTTParty.get(search_url, headers: {
        'User-Agent' => 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Accept' => 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language' => 'zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3',
      })
puts(response,"response")
      if response.code == 200
        doc = Nokogiri::HTML(response.body)
        
        # 查找产品链接
        product_link = doc.css('.pro-intro a').first&.[]('href')
        if product_link
          product_url = product_link.start_with?('//') ? "https:#{product_link}" : product_link
          scrape_product_page(product_url, product_name)
        else
          puts "未找到产品 #{product_name} 的页面链接"
        end
      else
        puts "搜索页面访问失败: #{response.code}"
      end
    rescue => e
      puts "处理产品 #{product_name} 时发生错误: #{e.message}"
    end
  end

  private

  def scrape_product_page(url, product_name)
    begin
      response = HTTParty.get(url, headers: {
        'User-Agent' => 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Accept' => 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
      })

      if response.code == 200
        doc = Nokogiri::HTML(response.body)
        
        # 查找大图链接
        image_urls = doc.css('.big-pic-box img').map { |img| 
          img['src']&.start_with?('//') ? "https:#{img['src']}" : img['src']
        }.compact.uniq

        puts "找到 #{image_urls.length} 张图片"
        image_urls.each_with_index do |url, index|
          download_single_image(url, product_name, index + 1)
        end
      else
        puts "获取产品页面失败: #{response.code}"
      end
    rescue => e
      puts "处理产品页面时发生错误: #{e.message}"
    end
  end

  def download_single_image(url, product_name, index)
    return if url.nil? || url.empty?

    begin
      uri = URI.parse(url)
      
      # 获取图片扩展名
      extension = File.extname(uri.path)
      extension = '.jpg' if extension.empty?
      
      # 创建安全的文件名
      safe_product_name = product_name.gsub(/[^0-9A-Za-z\-]/, '_')
      filename = File.join(@output_dir, "#{safe_product_name}_#{index}#{extension}")
      
      # 下载并保存图片
      URI.open(url) do |image|
        File.open(filename, 'wb') do |file|
          file.write(image.read)
        end
      end
      
      puts "✓ 成功下载: #{filename}"
    rescue => e
      puts "× 下载失败 (#{product_name} - 图片 #{index}): #{e.message}"
    end
  end
end

# 使用示例
if ARGV.empty?
  puts "请提供Excel文件路径，例如: ruby zol_image_scraper.rb products.xlsx"
else
  scraper = ZOLImageScraper.new(ARGV[0])
  scraper.scrape_all_products
end 