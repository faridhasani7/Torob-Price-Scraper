from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from difflib import SequenceMatcher
import requests
import json
import datetime
import time
import random
import traceback
import pandas as pd

GOOGLE_VERIFIED = False


def google_search_selenium(driver, query, cell_value):
    """
    Perform Google search using Selenium and return links that contain 'torob.'.
    """
    global GOOGLE_VERIFIED
    try:
        # Open Google homepage
        driver.get("https://google.com")
        search_box = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "q"))
        )

        # Wait for user verification if necessary
        if not GOOGLE_VERIFIED:
            input("Please complete Google verification then press Enter.")
            GOOGLE_VERIFIED = True

        search_box.clear()
        human_like_typing(search_box, query)
        search_box.submit()

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "g"))
        )

        results = driver.find_elements(By.CLASS_NAME, "g")
        num = 0
        all_links = []
        
        for result in results:
            title_elem = result.find_element(By.TAG_NAME, "h3")
            link_elem = result.find_element(By.TAG_NAME, "a")
            
            title = title_elem.text
            link = link_elem.get_attribute("href")
            
            # Remove prefix "خرید و قیمت " if present
            if title.startswith("خرید و قیمت "):
                title = title[12:]
            
            similarity_percent = similarity_ratio(to_en(title).lower(), to_en(cell_value).lower())
            
            if "torob." in link:
                all_links.append((f"{cell_value} _ {num + 1}", similarity_percent, link))
            
            num += 1
        
        # Sort links based on similarity ratio
        all_links.sort(key=lambda x: x[1], reverse=True)
        return all_links

    except Exception as error:
        log_exception_to_file(error, "google search selenium func")
        return None
    

def get_torob_info(url, product):
    try:
        r = requests.get(url)
        json_info = r.text.split('application/ld+json">')[1].split('</script')[0]
        dict_info = json.loads(json_info)

        if 'offers' in dict_info and 'offers' in dict_info['offers']:
            dict_info['offers']['offers'].sort(key=lambda x: float('inf') if int(x['price']) == 0 else int(x['price']))
            
            info_target = {}

            for i in range(4):
                if i < len(dict_info['offers']['offers']):
                    offer = dict_info['offers']['offers'][i]

                    info_target[f"{product}_{i}"] = {
                        'name': offer['name'],
                        'price': offer['price'],
                        'link': offer['url']
                    }
                else:
                    info_target[i] = {
                        'name': 'N/A',
                        'price': 'N/A',
                        'link': 'N/A'
                    }

            if all(info['price'] == 'N/A' for info in info_target.values()):
                return "no seller"

            return info_target

        else:
            return "no seller"

    except Exception as error:
        log_exception_to_file(error, "get torob info func")
        return "error"


def create_driver():
    try:
        chrome_options = Options()
        #chrome_options.add_argument('--headless')  # بدون نمایش پنجره
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('--start-maximized')
        prefs = {
            'profile.default_content_setting_values.notifications': 2,
            'credentials_enable_service': False,
            'profile.password_manager_enabled': False,
            'webrtc.ip_handling_policy': 'disable_non_proxied_udp',
            'webrtc.multiple_routes_enabled': False,
            'webrtc.nonproxied_udp_enabled': False
        }
        chrome_options.add_experimental_option('prefs', prefs)
        driver = webdriver.Chrome(options=chrome_options)

        return driver
    
    except Exception as error:
        log_exception_to_file(error, "creat driver func")


def log_exception_to_file(exception, reason, file_path="logs/error_log.txt"):
    """
    Log exceptions with timestamp and traceback to a file.
    """
    with open(file_path, "a", encoding='utf8') as file:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        exception_type = type(exception).__name__
        exception_message = str(exception)
        traceback_info = traceback.format_exc()
        file.write(f"Handling: {reason}\n")
        file.write(f"Timestamp: {timestamp}\n")
        file.write(f"Exception Type: {exception_type}\n")
        file.write(f"Exception Message: {exception_message}\n")
        file.write("Traceback:\n")
        file.write(traceback_info)
        file.write("\n" + "="*40 + "\n\n")


def to_en(text):
    try:
        l=[ "۰", "۱", "۲", "۳", "۴", "۵", "۶", "۷", "۸", "۹" ]

        for i in range(0, 10):
            text=text.replace(l[i], str(i))

        return text
    
    except Exception as error:
        log_exception_to_file(error, "to en func")


def similarity_ratio(str1, str2):
    try:
        ratio = SequenceMatcher(None, str1, str2).ratio()
        percentage = ratio * 100

        return percentage
    
    except Exception as error:
        log_exception_to_file(error, "similarity ratio func")


def human_like_typing(element, text):
    """
    Simulate human typing by sending keys with a random delay.
    """
    try:
        for char in text:
            element.send_keys(char)
            time.sleep(random.uniform(0.01, 0.1))
    except Exception as error:
        log_exception_to_file(error, "human like typing func")


# return just the best similarity link
# در آینده این رو باید عوض کنیم که به ترتیب شبیه بودن با سرچ ما هست را اولویت بندی کند.
def find_best_link_torob(google_result):
    try:
        max_item = max(google_result.items(), key=lambda item: list(item[1].keys())[0])
        max_value = list(max_item[1].keys())[0]
        max_link = max_item[1][max_value]

        return max_link

    except Exception as error:
        log_exception_to_file(error, "find target link torob func")


def write_to_json_file(data, filename):
    try:

        with open(filename, 'r', encoding='utf-8') as file:
            existing_data = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        existing_data = {}
    existing_data.update(data)

    with open(filename, 'w', encoding='utf-8') as file:
        json.dump(existing_data, file, ensure_ascii=False, indent=4)


def read_product_from_excel(file_path="excel/EXCEL.xlsx"):
    try:
        df = pd.read_excel(file_path)
        product_names = df['PRODUCT NAME'].tolist()
        
        return product_names
    
    except Exception as error:
        log_exception_to_file(error, "read product from excel func")


def write_info_to_excel(js, df):
    try:
        for index, row in df.iterrows():
            product_name = df.iloc[index, 1] # نام محصول
            if product_name in js: #بررسی میکنیم توی جیسان هست یا نه
                #از حلقه استفاده میکنیم که بنویسیم.
                sellers = js[product_name]
                #اینجا ما یک دیکشنری داریم که توش 4 تا عدد هست و ما باید این 4 عدد رو بندازیم توی جدول excel.
                #من از ی معادله ریاضی استفاده میکنم. برای نوشتن توی فایل excel, نیازه ما ردیف و ستون رو مشخص کنیم. ردیف توی index هست. ستون رو باید حساب کنیم که کجا میخوایم ذخیره بشه.
                #اولین ستونی که میخوایم ذخیره بشه، ستون شماره 4 هست که با حالت برنامه نویسیش میشه 3. بعدیش 5 هست. بعدیش 7 و بعدیش 9.
                #ما اگه بگیم: 3 + (id * 2), معادلمون درست میشه. Id اول 0 هست، در میاد 3. دومی 1 هست، در میاد 5 و تا آخر. پس:
                for id, data in sellers.items():
                    id = id.split("_")[-1]
                    id = int(id)
                    #شماره ستون نام فروشنده:
                    seller_name_ind = 3 + (int(id) * 2)
                    #اسم و قیمت
                    name = data['name']
                    price = data['price']
                    if name =="N/A": name = "no seller"
                    if price == "N/A": price = "no seller"
                    df.iloc[index, seller_name_ind] = name
                    df.iloc[index, seller_name_ind + 1] = price

            else:
                #اضافه کردن not found
                for ind in range(3, 10):
                    df.iloc[index, ind] = "not found"

        return df

    except Exception as error:
        log_exception_to_file(error, "write info to excel func")


def convert_json_to_excel(file_path="excel/EXCEL.xlsx"):
    try:
        df = pd.read_excel(file_path)
        with open("output/output_torob.json", "r", encoding='utf8') as fl:
            js = json.load(fl)
        df = write_info_to_excel(js, df)
        df.to_excel(file_path.replace('.xlsx', '_new.xlsx'), index=False)

    except Exception as error:
        log_exception_to_file(error, "convert json to excel func")


def sort_result_google_by_similarity(file_path='output/output_result_google.json'):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)

        for product, details in data.items():
            sorted_details = {}
            for sub_key in sorted(details, key=lambda k: -float(list(details[k].keys())[0])):
                sorted_details[sub_key] = details[sub_key]
            data[product] = sorted_details

        with open(file_path, 'w', encoding='utf-8') as file:
            json.dump(data, file, ensure_ascii=False, indent=4)

    except Exception as error:
        log_exception_to_file(error, "sort result google by similarity func")


def convert_jason_to_excel(name, file_path="excel/monitor.xlsx"):
    import pandas as pd
    import json

    # خواندن فایل JSON
    with open('output/output_torob.json', 'r', encoding='utf-8') as file:
        json_data = json.load(file)

    # خواندن فایل اکسل ورودی
    input_file = file_path  # نام فایل اکسل ورودی
    df = pd.read_excel(input_file)

    # اطمینان از اینکه ستون‌ها به نوع داده‌ی رشته (str) تبدیل شوند
    df["FIRST SELLER"] = df["FIRST SELLER"].astype(str)
    df["FIRST PRICE"] = df["FIRST PRICE"].astype(str)
    df["SECOND SELLER"] = df["SECOND SELLER"].astype(str)
    df["SECOND PRICE"] = df["SECOND PRICE"].astype(str)
    df["THIRD SELLER"] = df["THIRD SELLER"].astype(str)
    df["THIRD PRICE"] = df["THIRD PRICE"].astype(str)
    df["FORTH SELLER"] = df["FORTH SELLER"].astype(str)
    df["FORTH PRICE"] = df["FORTH PRICE"].astype(str)

    # پردازش و افزودن داده‌ها به اکسل
    for index, row in df.iterrows():
        product_name = row['PRODUCT NAME']  # نام محصول از اکسل

        # بررسی وجود محصول در داده‌های JSON
        if product_name in json_data:
            product_data = json_data[product_name]
            sellers_prices = []

            # استخراج اطلاعات فروشنده و قیمت
            for key, value in product_data.items():
                sellers_prices.append((value["name"], value["price"]))

            # پر کردن داده‌ها در اکسل
            for i in range(len(sellers_prices)):
                seller_column = f'{["FIRST", "SECOND", "THIRD", "FORTH"][i]} SELLER'
                price_column = f'{["FIRST", "SECOND", "THIRD", "FORTH"][i]} PRICE'
                df.at[index, seller_column] = str(sellers_prices[i][0])  # فروشنده
                df.at[index, price_column] = str(sellers_prices[i][1])  # قیمت

    # ذخیره فایل اکسل خروجی
    output_file = f'output_{name}.xlsx'
    df.to_excel(output_file, index=False)  # حذف پارامتر encoding

    print("فایل اکسل به‌روزرسانی شد و ذخیره شد.")