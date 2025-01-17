require 'nokogiri'
require 'httparty'
require 'open-uri'
require 'fileutils'
require 'roo'
require 'mini_magick'

class ProductImageScraper
  def initialize(excel_path)
    @excel_path = excel_path
    @output_dir = "product_images"
    FileUtils.mkdir_p(@output_dir)
  end

  def read_products_from_excel
    workbook = Roo::Spreadsheet.open(@excel_path)
    sheet = workbook.sheet(0)
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
    puts "从Excel中读取到 #{products.length} 个产品"

    products.each do |product|
      download_product_images(product)
    end
  end

  private

  def download_product_images(product_name)
    begin
      url = "https://www.bing.com/images/search?q=#{URI.encode_www_form_component(product_name)}"
      response = HTTParty.get(url, headers: {
        'User-Agent' => 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
      })

      if response.code == 200
        doc = Nokogiri::HTML(response.body)
        image_urls = doc.css('img.mimg').map { |img| img['src'] }.compact.first(5) # 每个产品下载前5张图片

        puts "\n开始下载 #{product_name} 的图片..."
        image_urls.each_with_index do |url, index|
          download_single_image(url, product_name, index + 1)
        end
      else
        puts "获取 #{product_name} 的图片链接失败: #{response.code}"
      end
    rescue => e
      puts "处理 #{product_name} 时发生错误: #{e.message}"
    end
  end

  def download_single_image(url, product_name, index)
    return if url.nil? || url.empty?

    begin
      # 下载图片并检测其实际类型
      tempfile = URI.open(url)
      image = MiniMagick::Image.read(tempfile)
      
      # 根据实际图片格式设置后缀
      extension = ".#{image.type.downcase}"
      
      # 创建安全的文件名（移除特殊字符）
      safe_product_name = product_name.gsub(/[^0-9A-Za-z\-]/, '_')
      filename = File.join(@output_dir, "#{safe_product_name}_#{index}#{extension}")
      
      # 保存图片
      FileUtils.cp(tempfile.path, filename)
      puts "✓ 成功下载: #{filename}"
    rescue => e
      puts "× 下载失败 (#{product_name} - #{index}): #{e.message}"
    ensure
      tempfile&.close
    end
  end
end

# 使用示例
if ARGV.empty?
  puts "请提供Excel文件路径，例如: ruby product_image_scraper.rb products.xlsx"
else
  scraper = ProductImageScraper.new(ARGV[0])
  scraper.scrape_images
end 