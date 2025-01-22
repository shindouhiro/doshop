const puppeteer = require('puppeteer');
const xlsx = require('xlsx');
const fs = require('fs');
const path = require('path');
const axios = require('axios');

class VivoImageScraper {
  constructor(excelPath) {
    this.excelPath = excelPath;
    this.outputDir = "product_images";
    fs.mkdirSync(this.outputDir, { recursive: true });

    console.log("\n初始化爬虫:");
    console.log(`- Excel文件路径: ${this.excelPath}`);
    console.log(`- 输出目录: ${this.outputDir}`);
  }

  async delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  async scrapeProductImages(productName, browser) {
    try {
      // 创建新页面
      const page = await browser.newPage();

      // 访问搜索页面
      console.log("\n访问搜索页面...");
      await page.goto("https://search.zol.com.cn/s/");

      // 等待搜索框和按钮加载
      await page.waitForSelector("#keyword");
      await page.waitForSelector(".search-btn");

      // 输入搜索关键词
      console.log(`输入搜索关键词: ${productName}`);
      await page.type("#keyword", productName);

      // 点击搜索按钮
      console.log("点击搜索按钮...");
      await page.click(".search-btn");

      // 等待搜索结果加载
      await this.delay(2000);

      // 查找产品标签
      const productTab = await page.$('.search-tab-nav.clearfix a[href*="detail.zol.com.cn"]');
      if (productTab) {
        console.log("找到产品标签");
        // 检查是否需要点击切换
        const isCurrentTab = await productTab.evaluate(el => el.classList.contains('current'));
        if (!isCurrentTab) {
          console.log("切换到产品标签...");
          await productTab.click();
          await this.delay(2000);
        }
      } else {
        console.log("未找到产品标签");
      }

      // 查找第一个产品链接
      const productLink = await page.$('.pro-intro h3 a');
      if (productLink) {
        console.log("找到产品链接");
        const productUrl = await productLink.evaluate(el => el.href);

        if (productUrl) {
          console.log(`产品URL: ${productUrl}`);

          // 获取当前页面句柄
          const currentPageTarget = page.target();

          // 点击链接访问产品页面
          await productLink.click();
          await this.delay(2000);

          // 等待新页面打开
          const newTarget = await browser.waitForTarget(target => target.opener() === currentPageTarget);
          const newPage = await newTarget.page();

          // 切换到新页面
          await newPage.bringToFront();

          // 获取新页面内容
          const content = await newPage.content();
          console.log('页面内容:', content);
          // 将页面内容写入文件
          const contentPath = path.join('content.txt');
          fs.writeFileSync(contentPath, content, 'utf8');
          console.log(`页面内容已保存到: ${contentPath}`);
          // 查找并点击参数链接
          const paramLink = await newPage.$('a[href*="/param.shtml"]');
          if (paramLink) {
            console.log("找到参数链接");
            await paramLink.click();
            await this.delay(2000);

            // 等待新页面加载
            const paramPageTarget = await browser.waitForTarget(target => target.url().includes('/param.shtml'));
            const paramPage = await paramPageTarget.page();
            await paramPage.bringToFront();

            // 获取参数页面内容
            const paramContent = await paramPage.content();
            console.log('参数页面内容已获取');

            // 获取参数表格内容
            const paramTable = await paramPage.$('.detailed-parameters table');
            if (paramTable) {
                const tableData = await paramPage.evaluate(table => {
                    const rows = Array.from(table.querySelectorAll('tr'));
                    return rows.map(row => {
                        const cells = Array.from(row.querySelectorAll('th, td'));
                        return cells.map(cell => cell.textContent.trim()).join('\t');
                    }).join('\n');
                }, paramTable);
                
                // 获取所有Excel文件
                const excelFiles = fs.readdirSync('.').filter(file => file.endsWith('.xlsx'));
                
                // 为每个Excel文件创建对应的目录并保存参数
                for (const excelFile of excelFiles) {
                    // 获取Excel文件名（不含扩展名）
                    const excelFileName = path.basename(excelFile, '.xlsx');
                    
                    // 创建Excel文件对应的目录
                    const excelDir = path.join('params', excelFileName);
                    fs.mkdirSync(excelDir, { recursive: true });
                    
                    // 在Excel目录下创建产品目录
                    const productDir = path.join(excelDir, productName.replace(/[/\\]/g, '_'));
                    fs.mkdirSync(productDir, { recursive: true });
                    
                    // 保存参数表格内容到对应产品文件夹
                    const paramContentPath = path.join(productDir, 'params.txt');
                    fs.writeFileSync(paramContentPath, tableData, 'utf8');
                    console.log(`参数表格内容已保存到: ${paramContentPath}`);
                }
            } else {
                console.log("未找到参数表格");
            }
            await paramPage.close();
          } else {
            console.log("未找到参数链接");
          }




          // 创建产品目录
          const productDir = path.join('images', productName.replace(/[/\\]/g, '_'));
          fs.mkdirSync(productDir, { recursive: true });
          console.log(`创建目录: ${productDir}`);

          // 查找所有图片元素
          const imageElements = await page.$$('.big-pic-box img');
          if (!imageElements.length) {
            console.log("未找到图片元素");
            return;
          }

          console.log(`找到 ${imageElements.length} 张图片`);

          // 下载每张图片
          for (let i = 0; i < imageElements.length; i++) {
            const imgUrl = await imageElements[i].evaluate(el => el.src);
            if (!imgUrl) {
              console.log(`图片 ${i + 1} 没有src属性`);
              continue;
            }

            // 确保URL是完整的
            const fullImgUrl = imgUrl.startsWith('http') ? imgUrl : `https:${imgUrl}`;

            // 构建保存路径
            const imgName = `${productName.replace(/[/\\]/g, '_')}_${i + 1}.jpg`;
            const imgPath = path.join(productDir, imgName);

            try {
              // 下载图片
              const response = await axios({
                method: 'get',
                url: fullImgUrl,
                responseType: 'stream',
                timeout: 10000
              });

              if (response.status === 200) {
                const writer = fs.createWriteStream(imgPath);
                response.data.pipe(writer);

                await new Promise((resolve, reject) => {
                  writer.on('finish', resolve);
                  writer.on('error', reject);
                });

                console.log(`已保存图片: ${imgName}`);
              } else {
                console.log(`下载图片 ${imgName} 失败: HTTP ${response.status}`);
              }
            } catch (error) {
              console.log(`下载图片 ${imgName} 时出错: ${error.message}`);
            }
          }
        } else {
          console.log("产品链接href属性为空");
        }
      } else {
        console.log("未找到产品链接");
      }

      await page.close();
    } catch (error) {
      console.log(`处理产品 ${productName} 时发生错误:`);
      console.log(`- 错误类型: ${error.constructor.name}`);
      console.log(`- 错误信息: ${error.message}`);
      console.log("- 错误堆栈:");
      console.log(error.stack.split('\n').slice(0, 6).join('\n'));
    }
  }

  async scrapeImages() {
    let browser;
    try {
      // 读取Excel文件
      const workbook = xlsx.readFile(this.excelPath);
      const worksheet = workbook.Sheets[workbook.SheetNames[0]];
      const data = xlsx.utils.sheet_to_json(worksheet);

      // 打印列名，帮助调试
      console.log("\nExcel文件包含以下列:");
      console.log(Object.keys(data[0]));

      // 检查是否存在"名称"列
      if (!data[0].hasOwnProperty('名称')) {
        console.log("\n错误: Excel文件中没有找到'名称'列");
        console.log("请确保Excel文件中包含'名称'列，或修改以下列名之一:");
        Object.keys(data[0]).forEach(col => {
          console.log(`- ${col}`);
        });
        return;
      }

      // 启动浏览器
      browser = await puppeteer.launch({
        headless: false,
        defaultViewport: null
      });

      // 遍历每个产品
      for (let i = 0; i < data.length; i++) {
        const productName = data[i]['名称'];
        console.log(`\n处理第 ${i + 1} 个产品: ${productName}`);
        await this.scrapeProductImages(productName, browser);
      }
    } catch (error) {
      console.log(`\n读取Excel文件时发生错误: ${error.message}`);
      console.log("请确保:");
      console.log("1. Excel文件存在且可访问");
      console.log("2. 文件格式正确（.xlsx或.xls）");
      console.log("3. 文件未被其他程序占用");
    } finally {
      if (browser) {
        await browser.close();
      }
    }
  }
}

// 运行爬虫
if (process.argv.length < 3) {
  console.log("请提供Excel文件路径，例如: node vivo_image_scraper.js products.xlsx");
} else {
  const scraper = new VivoImageScraper(process.argv[2]);
  scraper.scrapeImages().catch(error => {
    console.log("\n程序执行出错:", error);
  });
} 
