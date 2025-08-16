from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import time

# ChromeDriver 경로
CHROMEDRIVER_PATH = 'C:/path/to/chromedriver.exe'  # 본인 환경에 맞게 수정

service = Service(CHROMEDRIVER_PATH)

chrome_options = Options()
chrome_options.add_argument('--headless')  # 필요 없으면 삭제 가능
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')

driver = webdriver.Chrome(service=service, options=chrome_options)

try:
    url = 'https://www.lotteon.com/p/product/LO2452455739?sitmNo=LO2452455739_2452455740&ch_no=100065&ch_dtl_no=1000030&entryPoint=pcs&dp_infw_cd=CHT&NaPm=ct%3Dme6m4u20%7Cci%3De0ead49ce1ac55056934edd50fe728b8ab5095b5%7Ctr%3Dslsl%7Csn%3D1243359%7Chk%3Dafca6f74ede307c0902501facc639073fde4ea74'
    driver.get(url)

    time.sleep(5)

    html = driver.page_source
    soup = BeautifulSoup(html, 'html.parser')

    reviews = soup.select('span.texting')

    print(f'총 리뷰 개수: {len(reviews)}')
    for i, review in enumerate(reviews, 1):
        print(f'{i}. {review.get_text(strip=True)}')

finally:
    driver.quit()
