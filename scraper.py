from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.action_chains import ActionChains
import time
import json
from datetime import datetime
import os

class YdlQAScraper:
    def __init__(self):
        self.options = webdriver.ChromeOptions()
        self.options.add_argument('--disable-gpu')
        self.options.add_argument('--no-sandbox')
        self.options.add_argument('--disable-dev-shm-usage')
        self.options.add_argument('--disable-software-rasterizer')
        self.driver = None

    def start_driver(self):
        """初始化瀏覽器驅動"""
        try:
            self.driver = webdriver.Chrome(options=self.options)
            self.driver.implicitly_wait(2)
            print("瀏覽器驅動初始化成功")
        except Exception as e:
            print(f"瀏覽器驅動初始化失敗: {str(e)}")
            raise e

    def close_driver(self):
        """關閉瀏覽器驅動"""
        try:
            if self.driver:
                self.driver.quit()
                print("瀏覽器驅動已關閉")
        except Exception as e:
            print(f"關閉瀏覽器驅動時發生錯誤: {str(e)}")

    def wait_for_element(self, by, value, timeout=5):
        """等待元素出現的通用方法"""
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((by, value))
            )
            return element
        except TimeoutException:
            print(f"等待元素 {value} 超時")
            return None

    def close_ads(self):
        """處理各種可能的廣告"""
        try:
            print("開始處理廣告...")
            # 處理頂部 banner
            try:
                close_banner = self.wait_for_element(By.CSS_SELECTOR, '.js_closeWrap')
                if close_banner and close_banner.is_displayed():
                    close_banner.click()
                    print("關閉了頂部banner")
                    time.sleep(1)
            except:
                print("未找到頂部banner或已關閉")

            # 處理newcomer廣告
            try:
                newcomer_control = self.wait_for_element(By.CSS_SELECTOR, 'a.newcomer-control')
                if newcomer_control and newcomer_control.is_displayed():
                    newcomer_control.click()
                    print("關閉了newcomer廣告")
                    time.sleep(1)
            except:
                print("未找到newcomer廣告或已關閉")

            return True
        except Exception as e:
            print(f"處理廣告時發生錯誤: {str(e)}")
            return False

    def remove_overlay(self):
        """移除遮擋元素"""
        try:
            # 等待頁面加載完成
            time.sleep(2)
            
            # 找到並移除發表評論按鈕和其他遮擋元素
            self.driver.execute_script("""
                function removeElement(selector) {
                    const element = document.querySelector(selector);
                    if(element) {
                        element.remove();
                        return true;
                    }
                    return false;
                }
                
                removeElement('.js_fabiaopinglun');
                removeElement('.suspensionBox');
                removeElement('.m-footer');
                
                // 移除可能的彈窗
                const dialogs = document.querySelectorAll('.dialog-container');
                dialogs.forEach(dialog => dialog.remove());
            """)
            print("已移除遮擋元素")
            return True
        except Exception as e:
            print(f"移除遮擋元素時發生錯誤: {str(e)}")
            return False

    def scroll_to_element(self, element):
        """滾動到指定元素"""
        try:
            self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", element)
            time.sleep(1)
        except Exception as e:
            print(f"滾動到元素時發生錯誤: {str(e)}")

    def expand_comments(self):
        """展開所有評論"""
        try:
            # 先移除遮擋元素
            self.remove_overlay()
            
            # 最大嘗試次數
            max_attempts = 10
            attempt = 0
            
            while attempt < max_attempts:
                try:
                    # 使用JavaScript獲取按鈕文本和狀態
                    button_info = self.driver.execute_script("""
                        const button = document.querySelector('.js_pinglunMore');
                        if (!button) return null;
                        return {
                            text: button.textContent.trim(),
                            isVisible: button.offsetParent !== null
                        };
                    """)
                    
                    if not button_info:
                        print("未找到展開按鈕，評論已完全展開")
                        break
                        
                    # 如果按鈕文本是"收起"，說明已經完全展開
                    if "收起" in button_info.get('text', ''):
                        print("評論已完全展開")
                        break
                        
                    # 如果按鈕不可見，退出循環
                    if not button_info.get('isVisible', False):
                        print("展開按鈕不可見，評論已完全展開")
                        break
                    
                    # 使用顯式等待查找展開按鈕
                    expand_button = WebDriverWait(self.driver, 5).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, '.js_pinglunMore'))
                    )
                    
                    # 滾動到按鈕位置
                    self.scroll_to_element(expand_button)
                    
                    # 確認按鈕文本是"展開"才點擊
                    button_text = expand_button.text.strip()
                    if "展开全部" not in button_text:
                        print(f"按鈕文本為 '{button_text}'，跳過點擊")
                        break
                    
                    # 點擊展開按鈕
                    self.driver.execute_script("arguments[0].click();", expand_button)
                    print(f"成功點擊展開按鈕 - 第{attempt + 1}次")
                    
                    # 等待新內容加載
                    time.sleep(2)
                    attempt += 1
                    
                except TimeoutException:
                    print("未找到更多展開按鈕，評論已完全展開")
                    break
                    
            # 最後再檢查一次按鈕狀態，確保不會收起評論
            self.driver.execute_script("""
                const button = document.querySelector('.js_pinglunMore');
                if (button && button.textContent.trim().includes('收起')) {
                    button.style.display = 'none';
                }
            """)
            
            return True
                
        except Exception as e:
            print(f"展開評論時發生錯誤: {str(e)}")
            return False

    def extract_question(self):
        """提取問題相關信息"""
        try:
            # 等待問題內容加載
            personal_info = self.wait_for_element(By.CSS_SELECTOR, '.p-personal')
            if not personal_info:
                raise Exception("無法找到提問者信息")

            # 提取提問者信息
            questioner = {
                'name': personal_info.find_element(By.CSS_SELECTOR, '.name').text.replace('**', ''),
                'time': personal_info.find_element(By.CSS_SELECTOR, '.time').text,
                'location': personal_info.find_element(By.CSS_SELECTOR, '.from').text
            }

            # 提取問題內容
            question_content = self.wait_for_element(By.CSS_SELECTOR, '.p-text')
            if not question_content:
                raise Exception("無法找到問題內容")

            # 提取問題統計信息
            info = self.wait_for_element(By.CSS_SELECTOR, '.p-info')
            if not info:
                raise Exception("無法找到問題統計信息")

            stats = {
                'read_count': info.find_element(By.CSS_SELECTOR, '.read').text,
                'like_count': info.find_element(By.CSS_SELECTOR, '.zan').text
            }

            return {
                'questioner': questioner,
                'content': question_content.text,
                'stats': stats
            }
        except Exception as e:
            print(f"提取問題時發生錯誤: {str(e)}")
            return None

    def extract_comments(self):
        """提取評論信息"""
        try:
            # 先展開所有評論
            self.expand_comments()
            
            # 等待評論區域加載完成
            time.sleep(2)
            
            # 獲取所有評論項目
            comment_items = self.driver.find_elements(By.CSS_SELECTOR, '.p-pinglun-content > ul > li.p-item')
            
            comments = []
            for item in comment_items:
                try:
                    # 提取評論者信息區域
                    personal = item.find_element(By.CSS_SELECTOR, '.p-personal dd')
                    
                    # 提取基本信息
                    comment_info = {
                        'author': personal.find_element(By.CSS_SELECTOR, '.name').text.replace('**', ''),
                        'time': personal.find_element(By.CSS_SELECTOR, '.time').text,
                        'location': personal.find_element(By.CSS_SELECTOR, '.from').text,
                        'content': '',
                        'quoted_text': None
                    }
                    
                    # 提取評論內容區域
                    content_div = item.find_element(By.CSS_SELECTOR, '.p-content')
                    
                    # 提取主要評論內容
                    content_p = content_div.find_element(By.CSS_SELECTOR, 'p:not(.tocontent)')
                    comment_info['content'] = content_p.text
                    
                    # 檢查是否有引用內容
                    try:
                        quote = content_div.find_element(By.CSS_SELECTOR, 'p.tocontent')
                        if quote:
                            quoted_text = quote.text
                            # 分割引用的作者和內容
                            parts = quoted_text.split('：', 1)
                            if len(parts) == 2:
                                comment_info['quoted_text'] = {
                                    'author': parts[0].replace('：', ''),  # 去掉可能的冒號
                                    'content': parts[1].strip()
                                }
                    except NoSuchElementException:
                        pass  # 沒有引用內容，保持 quoted_text 為 None
                        
                    comments.append(comment_info)
                        
                except Exception as e:
                    print(f"處理單個評論時發生錯誤: {str(e)}")
                    continue
                    
            print(f"總共提取到 {len(comments)} 條評論")
            return comments
                
        except Exception as e:
            print(f"提取評論時發生錯誤: {str(e)}")
            return []

    def save_current_html(self, prefix="debug_page"):
        """保存當前頁面的HTML"""
        try:
            # 獲取當前頁面的HTML
            page_source = self.driver.page_source
            
            # 生成文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{prefix}_{timestamp}.html"
            
            # 保存HTML
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(page_source)
                
            print(f"HTML已保存到: {filename}")
            return filename
        except Exception as e:
            print(f"保存HTML時發生錯誤: {str(e)}")
            return None

    def scrape_url(self, url):
        """主要爬取函數"""
        try:
            print(f"開始爬取網址: {url}")
            self.start_driver()
            
            # 設置頁面加載超時
            self.driver.set_page_load_timeout(30)
            
            # 訪問頁面
            self.driver.get(url)
            print("成功載入頁面")
            
            # 等待頁面主要內容加載
            self.wait_for_element(By.CSS_SELECTOR, '.p-detail-content')
            print("頁面主要內容已加載")
            
            # 處理廣告和彈窗
            self.close_ads()
            
            # 提取數據
            data = {
                'url': url,
                'scrape_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'question': self.extract_question(),
                'comments': self.extract_comments()
            }
            
            # 保存數據
            filename = f"ydl_qa_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"數據已保存到 {filename}")
            
            return data
            
        except Exception as e:
            print(f"爬取過程中發生錯誤: {str(e)}")
            return None
        finally:
            self.close_driver()
    def is_valid_page(self):
        """檢查頁面是否有效（非空或錯誤頁面）"""
        try:
            # 檢查是否存在錯誤提示
            error_elements = self.driver.find_elements(By.CSS_SELECTOR, '.error-tip, .error-page')
            if error_elements:
                return False
                
            # 檢查是否存在主要內容
            content = self.wait_for_element(By.CSS_SELECTOR, '.p-detail-content', timeout=5)
            if not content:
                return False
                
            return True
        except Exception:
            return False
            
    def create_output_directory(self):
        """創建輸出目錄"""
        output_dir = f"ydl_qa_data_{datetime.now().strftime('%Y%m%d')}"
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        return output_dir
        
    def scrape_url_range(self, start_id, end_id):
        """批量爬取指定範圍內的URL"""
        try:
            print(f"開始批量爬取ID範圍: {start_id} 到 {end_id}")
            self.start_driver()
            
            # 創建輸出目錄
            output_dir = self.create_output_directory()
            
            # 記錄成功和失敗的URL
            results = {
                'success': [],
                'failed': [],
                'empty': []
            }
            
            for id_num in range(start_id, end_id + 1):
                url = f'https://m.ydl.com/ask/{id_num}'
                try:
                    print(f"\n正在處理 ID: {id_num}")
                    print(f"URL: {url}")
                    
                    # 訪問頁面
                    self.driver.get(url)
                    
                    # 檢查頁面是否有效
                    if not self.is_valid_page():
                        print(f"ID {id_num} 為空頁面或無效頁面，跳過")
                        results['empty'].append(id_num)
                        continue
                    
                    # 處理廣告和彈窗
                    self.close_ads()
                    
                    # 提取數據
                    data = {
                        'url': url,
                        'scrape_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        'question': self.extract_question(),
                        'comments': self.extract_comments()
                    }
                    
                    # 保存數據
                    filename = os.path.join(output_dir, f"ydl_qa_{id_num}.json")
                    with open(filename, 'w', encoding='utf-8') as f:
                        json.dump(data, f, ensure_ascii=False, indent=2)
                        
                    print(f"成功保存ID {id_num} 的數據")
                    results['success'].append(id_num)
                    
                    # 添加延遲以避免訪問過快
                    time.sleep(2)
                    
                except Exception as e:
                    print(f"處理 ID {id_num} 時發生錯誤: {str(e)}")
                    results['failed'].append(id_num)
                    continue
                    
            # 保存爬取結果摘要
            summary = {
                'crawl_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'total_processed': end_id - start_id + 1,
                'successful': len(results['success']),
                'failed': len(results['failed']),
                'empty': len(results['empty']),
                'success_ids': results['success'],
                'failed_ids': results['failed'],
                'empty_ids': results['empty']
            }
            
            summary_file = os.path.join(output_dir, 'crawl_summary.json')
            with open(summary_file, 'w', encoding='utf-8') as f:
                json.dump(summary, f, ensure_ascii=False, indent=2)
                
            print("\n爬取完成，結果摘要：")
            print(f"總處理數量: {summary['total_processed']}")
            print(f"成功數量: {summary['successful']}")
            print(f"失敗數量: {summary['failed']}")
            print(f"空頁面數量: {summary['empty']}")
            print(f"詳細結果已保存至: {summary_file}")
            
            return summary
            
        except Exception as e:
            print(f"批量爬取過程中發生錯誤: {str(e)}")
            return None
        finally:
            self.close_driver()

if __name__ == "__main__":
    scraper = YdlQAScraper()
    # 設定要爬取的ID範圍
    result = scraper.scrape_url_range(949782, 949790)
    
    # if result:
    #     print("\n爬取結果摘要:")
    #     print(f"問題: {result['question']['content'][:50]}...")
    #     print(f"評論數量: {len(result['comments'])}")