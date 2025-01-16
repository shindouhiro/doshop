require 'nokogiri'
require 'httparty'
require 'open-uri'
require 'fileutils'

class VivoImageScraper
  def initialize
    @search_term = "vivo X200 Pro"
    @output_dir = "vivo_images"
    FileUtils.mkdir_p(@output_dir)
  end

  def scrape_images
    begin
      # Using Bing Images as an example source
      url = "https://www.bing.com/images/search?q=#{URI.encode_www_form_component(@search_term)}"
      response = HTTParty.get(url, headers: {
        'User-Agent' => 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
      })

      if response.code == 200
        doc = Nokogiri::HTML(response.body)
        image_urls = doc.css('img.mimg').map { |img| img['src'] }.compact

        puts "找到 #{image_urls.length} 张图片"
        download_images(image_urls)
      else
        puts "请求失败: #{response.code}"
      end
    rescue => e
      puts "发生错误: #{e.message}"
    end
  end

  private

  def download_images(urls)
    urls.each_with_index do |url, index|
      begin
        next if url.nil? || url.empty?
        
        extension = File.extname(url).empty? ? '.jpg' : File.extname(url)
        filename = File.join(@output_dir, "vivo_x200_pro_#{index + 1}#{extension}")
        
        URI.open(url) do |image|
          File.open(filename, 'wb') do |file|
            file.write(image.read)
          end
        end
        
        puts "成功下载图片: #{filename}"
      rescue => e
        puts "下载图片失败 #{url}: #{e.message}"
      end
    end
  end
end

# 运行爬虫
scraper = VivoImageScraper.new
scraper.scrape_images 