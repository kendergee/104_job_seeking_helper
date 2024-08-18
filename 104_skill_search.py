from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

# 設置 user-agent
chrome_options = Options()
chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36")
chrome_options.add_argument("--disable-notifications")
chrome_options.add_argument("--disable-popup-blocking")
chrome_options.add_argument("--disable-infobars")
chrome_options.add_argument("--disable-extensions")

# 初始化 WebDriver，並添加 user-agent 設置
driver = webdriver.Chrome(options=chrome_options)

# 打開目標網頁
driver.get('https://www.104.com.tw/jobs/search/?ro=0&jobcat=2007001018,2007001021,2007001022,2007001020,2007001012&keyword=%E6%95%B8%E6%93%9A%E5%88%86%E6%9E%90&expansionType=area,spec,com,job,wf,wktm&jobexp=1&jobsource=cmw_redirect&langFlag=0&langStatus=0&recommendJob=1&hotJob=1')
driver.implicitly_wait(20)

# 等待第一筆搜索結果元素出現並可點擊
try:
    first_job = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, 'div[class*="b-block__left"] a[href*="/job/"]'))
    )
    first_job.click()

    tool_elements = WebDriverWait(driver,20).until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR,'a[class*="tools text-gray-deep-dark d-inline-block"]'))
    )

    tools = [element.text.strip() for element in tool_elements]
    print(tools)
except Exception as e:
    print(f"等待或點擊第一筆搜索結果時發生錯誤: {repr(e)}")

# 等待一段時間，觀察網頁反應
time.sleep(10)

# 關閉瀏覽器
driver.quit()