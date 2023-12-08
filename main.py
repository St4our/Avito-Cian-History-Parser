import logging
import re
import os
from datetime import datetime, timedelta, time
from itertools import groupby
from time import sleep
import csv
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


from hcaptcha_solver import hcaptcha_solver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (NoSuchElementException, TimeoutException)
from selenium.webdriver.support.ui import WebDriverWait
from bs4 import BeautifulSoup as BS
import urllib.request
import pytesseract
from PIL import Image

from root_chromedriver import RootChromeDriver, ChromeDriver
from cfg import * 



def send_email_msg(body_msg, subject_msg, send_from, password, send_to):
    # Create a secure SSL/TLS context
    context = ssl.create_default_context()
    with smtplib.SMTP(MAIL_HOST, MAIL_PORT) as smtp:
        smtp.ehlo()
        smtp.starttls(context=context)
        
        # Login with the provided credentials
        smtp.login(send_from, password)
        
        # Compose the message
        msg = MIMEMultipart()
        msg["From"] = send_from
        msg["To"] = send_to
        msg["Subject"] = subject_msg
        msg.attach(MIMEText(body_msg, "plain"))
        
        # Send the message
        send_errors = smtp.sendmail(from_addr=send_from, to_addrs=send_to, msg=msg.as_string())
        return send_errors

# def send_email_msg(driver, msg, subject, send_to):
#     print(f'[+]Start send [{msg}] msg to [{send_to}] user, using mail.ru service')
#     for _ in range(5):  # attempts to login
#         print('[!]Try to login...')
#         driver.get('https://e.mail.ru/inbox/')
#         sleep(2)
#         try:
#             WebDriverWait(driver=driver, timeout=6).until(
#                 EC.url_contains('login?')
#             )
#         except TimeoutException:
#             print('[+]Already login in the email')
#             break
#         else:
#             login_input = WebDriverWait(driver=driver, timeout=4).until(
#                 EC.presence_of_element_located((By.XPATH, '//input[@autocomplete="username"]'))
#             )
#             login_input.send_keys(EMAIL_LOGIN)
#             sleep(3)
#             # set remember checkbox
#             remember_checkbox = driver.find_element(By.XPATH, '//div[@class="save-auth-field-wrap"]')
#             remember_status = remember_checkbox.get_attribute('data-checked')
#             if remember_status == 'false':
#                 print('[+]Remember checkbox set')
#                 remember_checkbox.click()
#                 sleep(2)
#             # find btn sumbit for next
#             driver.find_element(By.XPATH, '//button[@data-test-id="next-button"]').click()
#             sleep(3)
#             password_input = WebDriverWait(driver=driver, timeout=4).until(
#                 EC.presence_of_element_located((By.XPATH, '//input[@type="password"]'))
#             )
#             password_input.send_keys(EMAIL_PASSWORD)
#             # set remember checkbox one more time
#             remember_checkbox = driver.find_element(By.XPATH, '//div[@class="save-auth-field-wrap"]')
#             remember_status = remember_checkbox.get_attribute('data-checked')
#             if remember_status == 'false':
#                 print('[+]Remember checkbox set (on password)')
#                 remember_checkbox.click()
#                 sleep(2)
#             # sumbit button
#             driver.find_element(By.XPATH, '//button[@data-test-id="submit-button"]').click()
#             sleep(3)
#             # waiting for load inbox
#             try:
#                 WebDriverWait(driver=driver, timeout=10).until(
#                     EC.url_contains('inbox/')
#                 )
#             except TimeoutException:
#                 print('[-]Unsuccess login')
#             else:
#                 print('[+]Success login')
#     # find write letter
#     WebDriverWait(driver=driver, timeout=10).until(
#         EC.presence_of_element_located((By.XPATH, "//div[@class='sidebar__header']//a[contains(@title, 'письмо')]"))
#     ).click()
#     sleep(3)  # for load
    
#     # enter send_to user mail to input
#     WebDriverWait(driver=driver, timeout=10).until(
#         EC.presence_of_element_located((By.XPATH, '//div[@data-type="to"]//input'))
#     ).send_keys(send_to)
#     sleep(2)

#     # enter the subject of the letter.
#     WebDriverWait(driver=driver, timeout=5).until(
#         EC.presence_of_element_located((By.XPATH, '//input[@name="Subject"]'))
#     ).send_keys(subject)
#     sleep(2)

#     # enter the message
#     WebDriverWait(driver=driver, timeout=5).until(
#         EC.presence_of_element_located((By.XPATH, '//div[@role="textbox"]'))
#     ).send_keys(msg)
#     sleep(2)

#     # send msg
#     WebDriverWait(driver=driver, timeout=3).until(
#         EC.presence_of_element_located((By.XPATH, '//button[@data-test-id="send"]'))
#     ).click()
#     sleep(2)

#     msg_links = WebDriverWait(driver=driver, timeout=10).until(
#         EC.presence_of_all_elements_located((By.XPATH, "//a[contains(@href, '/sent/')][text()='Письмо отправлено']"))
#     )
#     if msg_links:
#         print('[+]Success send message')
#     else:
#         print('[?]Send message')



def cian_parse_cards(driver, collected_cards):
    # wait cards loading
    WebDriverWait(driver, 10).until(
        EC.presence_of_all_elements_located((By.XPATH, '//div[@data-testid="offer-card"]'))
    )
    cards_count_elem = driver.find_element(By.XPATH, '//div[@class="_93444fe79c--wrapper--W0WqH"]')
    cards_count = int(cards_count_elem.get_property('childElementCount')) if cards_count_elem else 0
    
    for card_n in range(1, cards_count+3):
        try:
            btn = driver.find_element(By.XPATH, f'//div[@class="_93444fe79c--wrapper--W0WqH"]/div[{card_n}]//button[@data-mark="PhoneButton"]')
        except NoSuchElementException:
            continue
        # scroll to btn
        ActionChains(driver)\
            .scroll_to_element(btn)\
            .move_to_element(btn)\
            .perform()
        btn.click()
        # accept number
        try:
            WebDriverWait(driver, 2, poll_frequency=1).until(
                EC.presence_of_element_located((By.XPATH, '//button//span[text()="Всё равно позвонить"]'))
            ).click()
            # btn_accept.click()
        except TimeoutException:
            pass
    html = driver.page_source
    # Создаем объект BeautifulSoup
    soup = BS(html, 'html.parser')
    cards = soup.find_all('div', {'data-testid': 'offer-card'})
    for card in cards:
        # изображения
        # images = [img['src'] for img in card.find_all('img')]
        link = card.find('a', class_='_93444fe79c--link--VtWj6').get('href')
        title = card.find('span', attrs={'data-mark': 'OfferTitle'}).text
        # right side
        right_elem = card.find('div', attrs={'data-name': 'BrandingLevelWrapper'})
        # owner_strings = right_elem.get('outerText').split('\n')
        # name_company = right_elem.find('div', class_='_93444fe79c--name-container--enElO').text.strip()
        id_ = link.split('suburban/')[1].replace('/', '')
        # id_ = name_company if name_company.startswith('ID') else None
        type_company = right_elem.find('div', class_='_93444fe79c--container--GyJAp').find('span').text.strip()
        phone = right_elem.find('span', attrs={'data-mark': 'PhoneValue'}).text.strip()
        
        # area = card.find('div', {'data-name': 'GeneralInfoSectionRowComponent'}).text.strip()
        price = card.find('span', {'data-mark': 'MainPrice'}).text.strip().replace('\xa0', ' ')
        # price = float(
        #     ''.join(list(filter(lambda s: s.isdigit() or s in ['.', ','], card.find('span', {'data-mark': 'MainPrice'}).text.strip()))).replace(',', '.')
        # )
        additional_address = ' | '.join(
            [e.find('a').text.strip() + ' ' + e.find('div').text.strip() for e in card.find_all('div', class_='_93444fe79c--container--w7txv')]).replace('\n', '|')
        address = additional_address + ' | ' + card.find('div', {'class': '_93444fe79c--labels--L8WyJ'}).text.strip().replace('\n', '|')

        electric = 'Не указано'
        gaz = 'Не указано'
        sewarage = 'Не указано'
        water = 'Не указано'
        area = 'Не указано'
        # request and collect this data
        driver.get(link)
        sleep(3)
        date_created_text = driver.find_element(By.XPATH, '//div[@data-testid="metadata-added-date"]').text
        date_created = date_created_text.split('Обновлено:')
        if len(date_created) > 1:
            date_created = date_created[1].strip()
            date_created = cian_convert_date(date_created)
        else:
            date_created = date_created[0].strip()
        try:
            views_data = driver.find_element(By.XPATH, '//button[@data-name="OfferStats"]').text
        except NoSuchElementException:
            continue
        else:
            total_views, today_views = views_data.split(', ')
            total_views, today_views = int(''.join(re.findall(r'\d+', total_views))), int(''.join(re.findall(r'\d+', today_views)))
            

        card_html = driver.page_source
        soup = BS(card_html, 'html.parser')
        params_elems = soup.find_all('div', attrs={'data-name': 'OfferSummaryInfoItem'})
        params_elems = [] if params_elems is None else params_elems
        # format_params_elems = [ for p in params_elems]
        for p in params_elems:
            if not p:
                continue
            p = p.text
            if 'Электричество' in p:
                electric = p.replace('Электричество', '').replace('\xa0', ' ')
            elif 'Газ' in p:
                gaz = p.replace('Газ', '').replace('\xa0', ' ')
            elif 'Канализация' in p:
                sewarage = p.replace('Канализация', '').replace('\xa0', ' ')
            elif 'Водоснабжение' in p:
                water = p.replace('Водоснабжение', '').replace('\xa0', ' ')
            elif 'Площадь' in p:
                area = p.replace('Площадь', '').replace('\xa0', '')
        
        dict_card = {
            'ad_name': title,
            'ad_total_views': total_views,
            # 'ad_today_views': today_views,
            'ad_id': id_,
            'ad_area': area,
            'ad_total_price': price,
            'ad_address': address,
            'ad_type_company': type_company,
            'ad_phone': phone,
            'ad_link': link,
            'ad_date_created': date_created,
            'electric': electric,
            'gaz': gaz,
            'water': water,
            'sewarage': sewarage,
            'parse_timestamp': str(datetime.now().strftime(TIMESTAMP_DT_FORMAT)),
        }
        if not any([dict_card['ad_id'] == dict_2_card['ad_id'] for dict_2_card in collected_cards]):
            print(dict_card)
            collected_cards.append(dict_card)       



def cian_parse(driver: ChromeDriver, region_id: str):
    region_id = str(region_id)

    collected_cards = []    # container ads
    ex = ''   # Doesnt have any exceptions on start function

    # we have a first page => &p=1
    page_url = f'https://www.cian.ru/cat.php?deal_type=sale&engine_version=2&object_type%5B0%5D=3&offer_type=suburban&p=1&region={region_id}'
    for page_n in range(1, 2):
        if page_n > 1:
            page_url = page_url.replace(f'&p={page_n-1}', f'&p={page_n}')
        # collect current (first) page and replace to 2 3 4 5...
        print(f'[*]Get - {page_url}')
        driver.get(page_url)
        driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.END)
        driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.END)
        # check that page is exists
        try:
            if page_n > 1:
                WebDriverWait(driver, 3, poll_frequency=1).until(
                    EC.url_contains(f'&p={page_n}')
                )
        except TimeoutException:
            return [collected_cards, ex]
        else:
            try:
                cian_parse_cards(driver, collected_cards)
            except Exception as ex:
                return [collected_cards, ex]

    return [collected_cards, ex]


def avito_driver_get_handler(driver, url):
    driver.get(url)
    try:
        WebDriverWait(driver, timeout=6, poll_frequency=2).until(
            EC.presence_of_element_located((By.XPATH, "//div[@class='h-captcha']/iframe"))
        )
    except TimeoutException:
        return
    else:
        print('[!]hCaptcha detected!, solving...')
        solver = hcaptcha_solver.Captcha_Solver(verbose=True)
        captcha_is_present = solver.is_captcha_present()
        print(f'Captcha is present flag - {captcha_is_present}.Solving...')
        solver.solve_captcha(driver)
        driver.find_element(By.XPATH, '//div[@class="h-captcha"]//button[@type="submit"]').click()
        sleep(6)
        return


def avito_ads_parse(driver, collected_ads):
    ads_count = driver.find_elements(By.CSS_SELECTOR, 'div[data-marker="item"]')
    ads_count = 0 if ads_count is None else len(ads_count)
    for ad_num in range(1, ads_count):
        ad_xpath = f'//div[@data-marker="item"][{ad_num}]'
        # Собираем цены в объявлениях потом метод get("content")
        # try:
        ad_price = driver.find_element(By.XPATH, ad_xpath + '//p[@data-marker="item-price"]').text.replace('\xa0', '').replace(r'\xa0', '')
        # ad_price = float(''.join(list(filter(lambda s: s.isdigit() or s in ['.', ','], ad_price))).replace(',', '.'))

        # Собираем url объявлений
        ad_url = driver.find_element(By.XPATH, ad_xpath + '//a[@data-marker="item-title"]').get_attribute("href")

        # Собираем названия объявлений
        # try:
        ad_name = driver.find_element(By.XPATH, ad_xpath + '//h3[@itemprop="name"]').text
        # except:
        #     ad_name = "Нет названия объявления"

        # Собираем удельные цены (за сотку и т.д.)  
        try:
            ad_unit_price = driver.find_element(By.XPATH, ad_xpath + '//div[@class="iva-item-priceStep-uq2CQ"]//span/p').text
        except NoSuchElementException:
            ad_unit_price = 'Нет удельной цены'
        # else:
            # ad_unit_price = float(
            #     ''.join(list(filter(
            #         lambda s: s.isdigit() or s in ['.', ',', ' '], ad_unit_price))).replace(',', '.').replace(' ', ''))
        # except:
            # ad_unit_price = "Нет удельной цены"

        
        # Переходим на страницу объявляние для сбора доп инфы
        if len(driver.window_handles) == 1: 
            driver.execute_script("window.open('', '_blank');")
        # Переключаемся на новое вкладка
        driver.switch_to.window(driver.window_handles[-1])
        # начинаем сбор до инфы
        avito_driver_get_handler(driver, ad_url)
        sleep(4)

        # собираем доп инфу
        ad_address = driver.find_element(By.XPATH, '//div[@itemprop="address"]').text.strip().replace('\n', '|')
        ad_id = driver.find_element(By.XPATH, '//span[@data-marker="item-view/item-id"]').text
        ad_id = re.search('\d+', ad_id)[0]
        ad_company_type = driver.find_element(By.XPATH, '//div[@data-marker="seller-info/label"]').text
        ad_publ_time = driver.find_element(By.XPATH, '//span[@data-marker="item-view/item-date"]').text
        ad_publ_time = avito_convert_date(ad_publ_time)
        ad_total_views = driver.find_element(By.XPATH, '//span[@data-marker="item-view/total-views"]').text
        ad_total_views = int(re.search('\d+', ad_total_views)[0])
        ad_today_views = driver.find_element(By.XPATH, '//span[@data-marker="item-view/today-views"]').text
        ad_today_views = int(re.search('\d+', ad_today_views)[0])

        # собираем инфу с категорий снизу

        ad_area_found_list = [e.text.replace('Площадь:', '').strip() for e in driver.find_elements(By.XPATH, '//li[@class="params-paramsList__item-appQw"]') if 'Площадь:' in e.text]
        ad_area = ad_area_found_list[0] if ad_area_found_list else ad_name
        
        # коммуникации
        ad_descr = driver.find_element(By.XPATH, '//div[@data-marker="item-view/item-description"]').text.lower()
        electric = 'Упоминаеться' if re.search('электр', ad_descr) else 'Не указано'
        gaz = 'Упоминаеться' if re.search('газ', ad_descr) else 'Не указано'
        sewarage = 'Упоминаеться' if re.search('канализа', ad_descr) else 'Не указано'
        water = 'Упоминаеться' if re.search('вод[ао]', ad_descr) else 'Не указано'

        # собираем номер телефона (после открытия телефооного банера, элементы ктегорий не видимы становяться)
        # поэтом парсинг телефона после категорий (в поледнюю очередь!!!)
        try:
            # Наводим курсор на кнопку телефона и нажимаем на нее для отображения картинки с номером телефона
            button_phone = driver.find_element(By.XPATH, '//button[@data-marker="item-phone-button/card"]')
            sleep(2)
            ActionChains(driver).move_to_element(button_phone).click(button_phone).perform()

            # Скачиваем img с номерами телефонов и кладем в папку "phone_num_imgs", проверив, есть ли она
            num_img_url = driver.find_element(By.XPATH, '//img[@data-marker="phone-popup/phone-image"]').get_attribute("src")
            if not os.path.exists("phone_num_imgs"):
                os.mkdir("phone_num_imgs")
            urllib.request.urlretrieve(num_img_url, f"phone_num_imgs/phone_img.png")

            # Открываем картинку с помощью PIL
            img = Image.open(f"phone_num_imgs/phone_img.png")

            # Распознаем текст телефона с картинки с помощью tesseract
            # custom_config = r"--oem3 --psm13"  # Настройки для tesseract, эти по сути автоматические https://help.ubuntu.ru/wiki/tesseractб, oem3 это это режим работы движка, он и так по умолчанию 3, но вот остальные режимы: 0 = Original Tesseract only. 1 = Neural nets LSTM only. 2 = Tesseract + LSTM. 3 = Default, based on what is available.
            phone_num = pytesseract.image_to_string(img).replace("\n", "")
            os.remove(f"phone_num_imgs/phone_img.png")
        except Exception as ex:
            print(ex)
            phone_num = "Не получилось выгрузить номер телефона"

        # Добавляем все сведения из объявления  в словарь
        ad_dict_new = {
            "ad_name": ad_name,
            'ad_area': ad_area,
            'ad_id': ad_id,
            "ad_link": ad_url,
            "ad_total_price": ad_price,
            'ad_type_company': ad_company_type,
            'gaz': gaz,
            'water': water,
            'sewarage': sewarage,
            'electric': electric,
            # "Описание объявления": ad_descr_title,
            "ad_unit_price": ad_unit_price,
            "ad_address": ad_address,
            "ad_date_created": ad_publ_time,
            'ad_total_views': ad_total_views,
            # 'ad_today_views': ad_today_views,
            "ad_phone": phone_num,
            'parse_timestamp': str(datetime.now().strftime(TIMESTAMP_DT_FORMAT)),
        }
        if not any([ad_dict_new['ad_id'] == ad_d['ad_id'] for ad_d in collected_ads]):
            print(ad_dict_new)
            collected_ads.append(ad_dict_new)
        # Переключаемся обратно на основное вкладка
        driver.switch_to.window(driver.window_handles[0])


def avito_parse(driver: ChromeDriver, region_id):
    
    collected_ads = []    # container ads
    ex = ''   # Doesnt have any exceptions on start function

    page_url = f'https://www.avito.ru/{region_id}/zemelnye_uchastki?cd=1&p=1'
    for page_n in range(1, 2):   
        if page_n > 1:
            page_url = page_url.replace(f'&p={page_n-1}', f'&p={page_n}')
        # collect current (first) page and replace to 2 3 4 5...
        print(f'[*]Get - {page_url}')
        avito_driver_get_handler(driver, page_url)

        # scroll down
        driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.END)
        driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.END)
        # check that page is exists
        try:
            if page_n > 1:
                WebDriverWait(driver, 3, poll_frequency=1).until(
                    EC.url_contains(f'&p={page_n}')
                )
        except TimeoutException:
            return [collected_ads, ex]
        # try:
        # avito_driver_get_handler(driver, url)
        # input('Enter captcha...')
        # Объект поиска объявлений
        # ad_search_title = driver.find_element(By.CSS_SELECTOR, 'div [data-marker="page-title/text"]').text
        # Все объявления на странице
        # Счетчик для нумерации файлов с номером телефона
        try:
            avito_ads_parse(driver, collected_ads)
        except Exception as ex:
            return [collected_ads, ex]
        # print(f"Обрабобтано объявлений: {count}")
        # Помещаем все данные в json файл
        # with open(f"avito_search_{str(datetime.time)}.json", "a", encoding='utf-8') as file:
        #     json.dump(collected_ads, file, indent=4, ensure_ascii=False)      

    return [collected_ads, ex]

def cian_convert_date(date_string):
    # Словарь для перевода названий месяцев
    months = {
        'янв': 1,
        'фев': 2,
        'мар': 3,
        'апр': 4,
        'май': 5,
        'июн': 6,
        'июл': 7,
        'авг': 8,
        'сен': 9,
        'окт': 10,
        'ноя': 11,
        'дек': 12
    }

    # Разбиваем строку на дату и время
    date, time = date_string.split(', ')
    hours, mins = [int(n) for n in time.split(':')]

    # Если в строке указано "сегодня" или "сегодня", то возвращаем текущую дату или вчерашнюю
    # время оставляем из строки
    if 'сегодня' in date:
        now = datetime.now()
        target_date = datetime(now.year, now.month, now.day, hours, mins)
    elif 'вчера' in date:
        now = datetime.now() - timedelta(days=1)
        target_date = datetime(now.year, now.month, now.day, hours, mins)
    else:
        # Разбиваем дату на день и месяц
        day, month = date.split(' ')
        # Получаем номер месяца из словаря
        month_number = months[month]
        # Возвращаем дату и время в формате YYYY-MM-DD HH:MM
        target_date = datetime(datetime.now().year, month_number, int(day), hours, mins)
    return target_date.strftime('%Y-%m-%d %H:%M')



def avito_convert_date(date_string):
    # Словарь для перевода названий месяцев
    months = {
        'января': 1,
        'февраля': 2,
        'марта': 3,
        'апреля': 4,
        'мая': 5,
        'июня': 6,
        'июля': 7,
        'августа': 8,
        'сентября': 9,
        'октября': 10,
        'ноября': 11,
        'декабря': 12
    }

    date_string = date_string.replace('· ', '')

    # Разбиваем строку на дату и время
    date, time = date_string.split(' в ')
    hours, mins = [int(re.search('\d+', n)[0]) for n in time.split(':')]

    # Если в строке указано "сегодня" или "сегодня", то возвращаем текущую дату или вчерашнюю
    # время оставляем из строки
    if 'сегодня' in date:
        now = datetime.now()
        target_date = datetime(now.year, now.month, now.day, hours, mins)
    elif 'вчера' in date:
        now = datetime.now() - timedelta(days=1)
        target_date = datetime(now.year, now.month, now.day, hours, mins)
    else:
        # Разбиваем дату на день и месяц
        day, month = date.split(' ')
        # Получаем номер месяца из словаря
        month_number = months[month]
        # Возвращаем дату и время в формате YYYY-MM-DD HH:MM
        target_date = datetime(datetime.now().year, month_number, int(day), hours, mins)
    return target_date.strftime('%Y-%m-%d %H:%M')



def update_total_csv(ads_data: list, fn):
    csv_ads_id = []
    if os.path.exists(fn):
        with open(fn, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            csv_ads_id = [str(row['ad_id']) for row in reader]

    # process ads_data
    process_ads_data = ads_data.copy()
    for ad in process_ads_data:
        del ad['parse_timestamp']
    
    # Сохранение данных в CSV файл
    with open(fn, 'a', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=process_ads_data[0].keys())
        
        # записать заголовки если файл новый
        if not csv_ads_id:
            writer.writeheader()

        # Write new data only if 'ad_id' not in csv_ads_id
        for ad in process_ads_data:
            if str(ad['ad_id']) not in csv_ads_id:
                writer.writerow(ad)


def read_history_csv(fn):
    data = []
    if os.path.exists(fn):
        with open(fn, 'r', newline='', encoding='utf-8') as file:
            reader = csv.reader(file)
            try:
                header = next(reader)  # Skip the header row
            except StopIteration:
                return data
    
            for key, group in groupby(reader, key=lambda row: row[0]):
                ad_data = {'ad_id': key, 'prices': [], 'views': []}
                for row in group:
                    parse_timestamp, ad_total_price, ad_total_views = row[1:]
                    if ad_total_price:
                        ad_data['prices'].append({'timestamp': parse_timestamp, 'ad_total_price': ad_total_price})
                    if ad_total_views:
                        ad_data['views'].append({'timestamp': parse_timestamp, 'ad_total_views': int(ad_total_views)})
                data.append(ad_data)
    return data


def update_history_csv(ads_data, fn):
    existing_ads = read_history_csv(fn)

    # update existing ads
    for ad in ads_data:
        ad_id = ad['ad_id']
        
        existing_ad = next((existing_ad for existing_ad in existing_ads if str(existing_ad['ad_id']) == str(ad_id)), None)

        if existing_ad:
            # Update existing ad with new prices and views
            existing_ad['prices'].insert(0, {'ad_total_price': ad['ad_total_price'], 'timestamp': ad['parse_timestamp']})
            existing_ad['views'].insert(0, {'ad_total_views': ad['ad_total_views'], 'timestamp': ad['parse_timestamp']})
        else:
            # Add new ad
            ad_dict = {
                'ad_id': ad_id, 
                'prices': [{'ad_total_price': ad['ad_total_price'], 'timestamp': ad['parse_timestamp']}], 
                'views': [{'ad_total_views': ad['ad_total_views'], 'timestamp': ad['parse_timestamp']}]
            }
            existing_ads.append(ad_dict)
    
    # Write the existing ads rows
    with open(fn, 'w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)

        # write headers because we rewrite ads
        writer.writerow(['ad_id', 'timestamp', 'ad_total_price', 'ad_total_views'])

        # Write the updated data to the file
        for ad in existing_ads:
            ad_id = ad['ad_id']
            
            # Extract and write price history
            for price, view in zip(ad.get('prices'), ad.get('views', [])):
                timestamp = price['timestamp']
                assert price['timestamp'] == view['timestamp'], f'View timestamp and price timestamp is not equal (ad_id - {ad_id})'
                ad_total_views = view['ad_total_views']
                ad_total_price = price['ad_total_price']
                ad_data = [ad_id, timestamp, ad_total_price, ad_total_views]
                writer.writerow(ad_data)



def sleep_to_point(point: datetime):
    ''' sleep program until not target time (point) '''
    
    get_remaining_secs = lambda: (
        point - datetime.now()).total_seconds()
    
    units = [(3600, 'hours'), (60, 'minutes'), (1, 'seconds')]
    for unit, name in units:
        units_count = 1
        while units_count > 0:
            remaining_sec = get_remaining_secs()
            units_count = (remaining_sec // unit)
            # print(f'Current sleep: {name.upper()} - {units_count}')
            if units_count > 0:
                # print('*sleep*')
                sleep(unit if name != 'seconds' else units_count)


# def write_execution_logs(text, fn='execution_log.txt'):
#     with open(fn, 'a', encoding='utf-8') as f:
#             f.write(text + '\n')


def main():
    # create logger
    logging.basicConfig(
        filename='execution.log', level=logging.INFO, 
        format='%(asctime)s - %(levelname)s - %(message)s',
        encoding='utf-8')

    while True:
        # (next program run in the 22:00)
        msg = f'Начало работы парсера'
        logging.info(msg)
        # write_execution_logs(msg)

        # check exceptions and send emails about it
        exceptions_msg = ''
    
        # set ocr tesseract path
        if not os.path.exists(TESSERACT_OCR_PATH):
            msg = f'EXCEPTION WITH FIND OCR_TESSERACT:\nProgramm was not found tesseract ocr .exe file ;(\n'
            print(msg)
            exceptions_msg += msg
            logging.error(msg)
        else:
            # save ocr path and start parsing
            pytesseract.pytesseract.tesseract_cmd = TESSERACT_OCR_PATH
            
            with RootChromeDriver()._init_local_driver() as driver:
                # parsing moskow and MO
                
                # avito
                avito_parsed = []
        
                try:
                    parsed_result = avito_parse(driver, AVITO_REGIONS['Москва и МО'])   
                except Exception as ex:
                    parsed_result = [[], f'AVITO REGION - [Москва и МО] GET EXCEPTION\n{ex}\n']
                else:
                    ex = parsed_result[1]
                    if ex:
                        parsed_result[1] = f'AVITO REGION - [Москва и МО] GET EXCEPTION\n{ex}\n'
                finally:
                    avito_parsed.append(parsed_result)
                
                # cian
        
                # create cian parsed for moskow and MO
                cian_parsed = []
                
                # extend cian parsed for Москва
                try:
                    parsed_result = cian_parse(driver, CIAN_REGIONS['Москва'])
                except Exception as ex:
                    parsed_result = [[], f'CIAN REGION - [Москва] GET EXCEPTION\n{ex}\n']
                else:
                    ex = parsed_result[1]
                    if ex:
                        parsed_result[1] = f'CIAN REGION - [Москва] GET EXCEPTION\n{ex}\n'
                finally:    
                    cian_parsed.append(parsed_result)
                
                # extend cian parsed for MO
                try:
                    parsed_result = cian_parse(driver, CIAN_REGIONS['Московская область'])
                except Exception as ex:
                    parsed_result = [[], f'CIAN REGION - [Московская область] GET EXCEPTION\n{ex}\n']
                else:
                    ex = parsed_result[1]
                    if ex:
                        parsed_result[1] = f'CIAN REGION - [Московская область] GET EXCEPTION\n{ex}\n'
                finally:
                    cian_parsed.append(parsed_result)
        
            # unpack avito_parsed
            try:
                avito_ads = []
                for ads, ex_str in avito_parsed:
                    avito_ads += ads
                    if ex_str:
                        exceptions_msg += ex_str
            except Exception as ex:
                msg = f'\nEXCEPTION WITH UNPACK AVITO PARSED DATA\n{ex}\n'
                exceptions_msg += msg
                logging.error(msg)
        
            # unpack cian_parsed
            try:
                cian_ads = []
                for ads, ex_str in cian_parsed:
                    cian_ads += ads
                    if ex_str:
                        exceptions_msg += ex_str
            except Exception as ex:
                msg += f'\nEXCEPTION WITH UNPACK CIAN PARSED DATA\n{ex}\n'
                exceptions_msg += msg
                logging.error(msg)
            
            # avito_ads = [
            #     {'parse_timestamp': str(datetime.now()), 'ad_name': 'Участок 20 сот. (промназначения)', 'ad_area': '20 сот.', 'ad_id': '2425395044', 'ad_link': 'https://www.avito.ru/moskva/zemelnye_uchastki/uchastok_20_sot._promnaznacheniya_2425395044', 'ad_total_price': 600000.0, 'ad_type_company': 'Агентство', 'gaz': 'Не указано', 'water': 'Не указано', 'sewarage': 'Не указано', 'electric': 'Не указано', 'ad_unit_price': 1138462.0, 'ad_address': 'Москва, Варшавское ш., 170\nСимферопольское шоссе', 'ad_date_created': '· вчера в 11:44', 'ad_total_views': 5023, 'ad_phone': '8 915 408-72-98'},
            #     {'parse_timestamp': str(datetime.now()), 'ad_name': 'Участок 6,5 сот. (ИЖС)', 'ad_area': 'Не указано', 'ad_id': '2391017532', 'ad_link': 'https://www.avito.ru/pavlovskaya_sloboda/zemelnye_uchastki/uchastok_65_sot._izhs_2391017532', 'ad_total_price': 7400000.0, 'ad_type_company': 'Частное лицо', 'gaz': 'Упоминаеться', 'water': 'Не указано', 'sewarage': 'Не указано', 'electric': 'Не указано', 'ad_unit_price': 1138462.0, 'ad_address': 'Московская область, г.о. Истра, д. Покровское, Новорижский б-р\nВолоколамское шоссе, 25 км', 'ad_date_created': '· вчера в 16:19', 'ad_total_views': 1197, 'ad_phone': '8 965 174-23-81'},
            #     {'parse_timestamp': str(datetime.now()), 'ad_name': 'Участок 5,5 сот. (ИЖС)', 'ad_area': '5.5 сот.', 'ad_id': '3906575970', 'ad_link': 'https://www.avito.ru/moskovskaya_oblast_troitskoe/zemelnye_uchastki/uchastok_55_sot._izhs_3906575970', 'ad_total_price': 1200000.0, 'ad_type_company': 'Агентство', 'gaz': 'Упоминаеться', 'water': 'Упоминаеться', 'sewarage': 'Не указано', 'electric': 'Не указано', 'ad_unit_price': 1138462.0, 'ad_address': 'Московская область, г.о. Домодедово, д. Минаево, коттеджный пос. Южный парк\nНовокаширское шоссе, 35 км', 'ad_date_created': '· 1 декабря в 09:43', 'ad_total_views': 708, 'ad_phone': 'Не получилось выгрузить номер телефона'}
            # ]
            
            # cian_ads = [
            #     {'parse_timestamp': str(datetime.now()), 'ad_name': 'Участок, 380 сот., ИЖС', 'ad_total_views': 2391, 'ad_id': '285820345', 'ad_area': '380сот.', 'ad_total_price': 90000000.0, 'ad_address': 'Калужское шоссе \nМосква, ТАО (Троицкий), Михайлово-Ярцевское поселение, д. Пудово-Сипягино', 'ad_type_company': 'Агентство недвижимости', 'ad_phone': '+7 962 369-02-16', 'ad_link': 'https://www.cian.ru/sale/suburban/285820345/', 'ad_date_created': 'сегодня, 09:15', 'electric': 'Есть', 'gaz': 'Есть', 'water': 'Есть', 'sewarage': 'Есть'},
            #     {'parse_timestamp': str(datetime.now()), 'ad_name': 'Участок, 30 сот., ИЖС', 'ad_total_views': 476, 'ad_id': '293882436', 'ad_area': '30сот.', 'ad_total_price': 9000000.0, 'ad_address': 'Киевское шоссе \nМосква, ТАО (Троицкий), Михайлово-Ярцевское поселение, Ярцево лайф кп', 'ad_type_company': 'Застройщик', 'ad_phone': '+7 962 363-97-64', 'ad_link': 'https://www.cian.ru/sale/suburban/293882436/', 'ad_date_created': '21 ноя, 04:02', 'electric': 'Не указано', 'gaz': 'Не указано', 'water': 'Есть', 'sewarage': 'Есть'},
            #     {'parse_timestamp': str(datetime.now()), 'ad_name': 'Участок, 30 сот., ИЖС', 'ad_total_views': 1129, 'ad_id': '291191736', 'ad_area': '30сот.', 'ad_total_price': 28900000.0, 'ad_address': 'Киевское шоссе \nРассудово \nМосква, ТАО (Троицкий), Новофедоровское поселение, д. Кузнецово, Вик кп', 'ad_type_company': 'Агентство недвижимости', 'ad_phone': '+7 964 792-63-98', 'ad_link': 'https://www.cian.ru/sale/suburban/291191736/', 'ad_date_created': '29 ноя, 17:28', 'electric': 'Есть', 'gaz': 'Есть', 'water': 'Не указано', 'sewarage': 'Не указано'},
            #     {'parse_timestamp': str(datetime.now()), 'ad_name': 'Участок, 5 сот.', 'ad_total_views': 223, 'ad_id': '295560844', 'ad_area': '5сот.', 'ad_total_price': 2500000.0, 'ad_address': 'Боровское шоссе \nРассудово \nМосква, ТАО (Троицкий), Новофедоровское поселение, Фаворит кп', 'ad_type_company': 'Застройщик', 'ad_phone': '+7 905 719-68-72', 'ad_link': 'https://www.cian.ru/sale/suburban/295560844/', 'ad_date_created': '1 дек, 13:50', 'electric': 'Есть', 'gaz': 'Не указано', 'water': 'Есть', 'sewarage': 'Есть'},
            #     {'parse_timestamp': str(datetime.now()), 'ad_name': 'Участок, 17 сот.', 'ad_total_views': 15939, 'ad_id': '260461141', 'ad_area': '17сот.', 'ad_total_price': 381488074.0, 'ad_address': 'Покровское-Стрешнево \nМосква, СЗАО, р-н Хорошево-Мневники, Таманская улица, вл111', 'ad_type_company': 'Агентство недвижимости', 'ad_phone': '+7 966 153-69-63', 'ad_link': 'https://www.cian.ru/sale/suburban/260461141/', 'ad_date_created': '29 ноя, 17:28', 'electric': 'Есть', 'gaz': 'Есть', 'water': 'Не указано', 'sewarage': 'Не указано'},
            #     {'parse_timestamp': str(datetime.now()), 'ad_name': 'Участок, 7.94 сот., ИЖС', 'ad_total_views': 53, 'ad_id': '293667889', 'ad_area': '7,94сот.', 'ad_total_price': 3176000.0, 'ad_address': 'Калужское шоссе \nМосква, ТАО (Троицкий), Вороновское поселение, д. Юрьевка', 'ad_type_company': 'Застройщик', 'ad_phone': '+7 967 209-09-70', 'ad_link': 'https://www.cian.ru/sale/suburban/293667889/', 'ad_date_created': '4 ноя, 07:40', 'electric': 'Есть', 'gaz': 'Есть', 'water': 'Есть', 'sewarage': 'Не указано'},
            #     {'parse_timestamp': str(datetime.now()), 'ad_name': 'Участок, 6 сот., ИЖС', 'ad_total_views': 1126, 'ad_id': '295044485', 'ad_area': '6сот.', 'ad_total_price': 2400000.0, 'ad_address': 'Калужское шоссе \nАпрелевка \nМосква, ТАО (Троицкий), Краснопахорское поселение, Цветочный кп, 215', 'ad_type_company': 'Агентство недвижимости', 'ad_phone': '+7 964 557-78-64', 'ad_link': 'https://www.cian.ru/sale/suburban/295044485/', 'ad_date_created': '2 дек, 10:16', 'electric': 'Есть', 'gaz': 'Магистральный по границе', 'water': 'Скважина', 'sewarage': 'Септик'},
            #     {'parse_timestamp': str(datetime.now()), 'ad_name': 'Участок, 6.78 сот.', 'ad_total_views': 19, 'ad_id': '295560868', 'ad_area': '6,78сот.', 'ad_total_price': 3390000.0, 'ad_address': 'Боровское шоссе \nРассудово \nМосква, ТАО (Троицкий), Новофедоровское поселение, Фаворит кп', 'ad_type_company': 'Застройщик', 'ad_phone': '+7 905 719-68-72', 'ad_link': 'https://www.cian.ru/sale/suburban/295560868/', 'ad_date_created': '1 дек, 13:50', 'electric': 'Есть', 'gaz': 'Не указано', 'water': 'Есть', 'sewarage': 'Есть'},
            #     {'parse_timestamp': str(datetime.now()), 'ad_name': 'Участок, 6 сот., ИЖС', 'ad_total_views': 5388, 'ad_id': '288572325', 'ad_area': '6сот.', 'ad_total_price': 2400000.0, 'ad_address': 'Калужское шоссе \nМосква, ТАО (Троицкий), Вороновское поселение, № 415 кв-л', 'ad_type_company': 'Агентство недвижимости', 'ad_phone': '+7 916 544-10-85', 'ad_link': 'https://www.cian.ru/sale/suburban/288572325/', 'ad_date_created': '2 дек, 10:14', 'electric': 'Есть', 'gaz': 'Магистральный по границе', 'water': 'Есть', 'sewarage': 'Есть'},
            #     {'parse_timestamp': str(datetime.now()), 'ad_name': 'Участок, 8.71 сот., ИЖС', 'ad_total_views': 223, 'ad_id': '295285529', 'ad_area': '8,71сот.', 'ad_total_price': 3427100.0, 'ad_address': 'Киевское шоссе \nМосква, ТАО (Троицкий), Михайлово-Ярцевское поселение, Ярцево лайф кп', 'ad_type_company': 'Застройщик', 'ad_phone': '+7 962 363-97-64', 'ad_link': 'https://www.cian.ru/sale/suburban/295285529/', 'ad_date_created': '21 ноя, 07:38', 'electric': 'Не указано', 'gaz': 'Не указано', 'water': 'Есть', 'sewarage': 'Есть'},
            #     {'parse_timestamp': str(datetime.now()), 'ad_name': 'Участок, 7 сот., ИЖС', 'ad_total_views': 406, 'ad_id': '295044779', 'ad_area': '7сот.', 'ad_total_price': 2800000.0, 'ad_address': 'Калужское шоссе \nМосква, ТАО (Троицкий), Вороновское поселение, № 10 кв-л', 'ad_type_company': 'Агентство недвижимости', 'ad_phone': '+7 964 557-78-64', 'ad_link': 'https://www.cian.ru/sale/suburban/295044779/', 'ad_date_created': '2 дек, 10:18', 'electric': 'Есть', 'gaz': 'Магистральный по границе', 'water': 'Скважина', 'sewarage': 'Септик'},
            #     {'parse_timestamp': str(datetime.now()), 'ad_name': 'Участок, 6.5 сот.', 'ad_total_views': 6, 'ad_id': '295560811', 'ad_area': '6,5сот.', 'ad_total_price': 3900000.0, 'ad_address': 'Боровское шоссе \nРассудово \nМосква, ТАО (Троицкий), Новофедоровское поселение, Фаворит кп', 'ad_type_company': 'Застройщик', 'ad_phone': '+7 905 719-68-72', 'ad_link': 'https://www.cian.ru/sale/suburban/295560811/', 'ad_date_created': '1 дек, 13:50', 'electric': 'Есть', 'gaz': 'Не указано', 'water': 'Есть', 'sewarage': 'Есть'},
            #     {'parse_timestamp': str(datetime.now()), 'ad_name': 'Участок, 7.9 сот., ИЖС', 'ad_total_views': 2356, 'ad_id': '288572574', 'ad_area': '7,9сот.', 'ad_total_price': 2800000.0, 'ad_address': 'Калужское шоссе \nМосква, ТАО (Троицкий), Вороновское поселение, № 415 кв-л', 'ad_type_company': 'Агентство недвижимости', 'ad_phone': '+7 916 544-10-85', 'ad_link': 'https://www.cian.ru/sale/suburban/288572574/', 'ad_date_created': '2 дек, 10:15', 'electric': 'Есть', 'gaz': 'Магистральный по границе', 'water': 'Есть', 'sewarage': 'Есть'},
            #     {'parse_timestamp': str(datetime.now()), 'ad_name': 'Участок, 9.8 сот., ИЖС', 'ad_total_views': 43, 'ad_id': '295285562', 'ad_area': '9,8сот.', 'ad_total_price': 4018000.0, 'ad_address': 'Киевское шоссе \nМосква, ТАО (Троицкий), Михайлово-Ярцевское поселение, Ярцево лайф кп', 'ad_type_company': 'Застройщик', 'ad_phone': '+7 962 363-97-64', 'ad_link': 'https://www.cian.ru/sale/suburban/295285562/', 'ad_date_created': '21 ноя, 07:38', 'electric': 'Не указано', 'gaz': 'Не указано', 'water': 'Есть', 'sewarage': 'Есть'},
            #     {'parse_timestamp': str(datetime.now()), 'ad_name': 'Участок, 7 сот., ИЖС', 'ad_total_views': 524, 'ad_id': '294728361', 'ad_area': '7сот.', 'ad_total_price': 2800000.0, 'ad_address': 'Калужское шоссе \nМосква, ТАО (Троицкий), Краснопахорское поселение, № 123 кв-л', 'ad_type_company': 'Риелтор', 'ad_phone': '+7 964 538-95-39', 'ad_link': 'https://www.cian.ru/sale/suburban/294728361/', 'ad_date_created': '2 дек, 10:08', 'electric': 'Есть', 'gaz': 'Магистральный по границе', 'water': 'Скважина', 'sewarage': 'Септик'},
            #     {'parse_timestamp': str(datetime.now()), 'ad_name': 'Участок, 13.63 сот., ИЖС', 'ad_total_views': 68, 'ad_id': '295285547', 'ad_area': '13,63сот.', 'ad_total_price': 4050000.0, 'ad_address': 'Киевское шоссе \nМосква, ТАО (Троицкий), Михайлово-Ярцевское поселение, Ярцево лайф кп', 'ad_type_company': 'Застройщик', 'ad_phone': '+7 962 363-97-64', 'ad_link': 'https://www.cian.ru/sale/suburban/295285547/', 'ad_date_created': '21 ноя, 07:38', 'electric': 'Не указано', 'gaz': 'Не указано', 'water': 'Есть', 'sewarage': 'Есть'},
            #     {'parse_timestamp': str(datetime.now()), 'ad_name': 'Участок, 12 сот., ИЖС', 'ad_total_views': 216, 'ad_id': '294728489', 'ad_area': '12сот.', 'ad_total_price': 4800000.0, 'ad_address': 'Калужское шоссе \nМосква, ТАО (Троицкий), Краснопахорское поселение, № 123 кв-л', 'ad_type_company': 'Риелтор', 'ad_phone': '+7 964 538-95-39', 'ad_link': 'https://www.cian.ru/sale/suburban/294728489/', 'ad_date_created': '2 дек, 10:09', 'electric': 'Есть', 'gaz': 'Магистральный по границе', 'water': 'Скважина', 'sewarage': 'Септик'},
            #     {'parse_timestamp': str(datetime.now()), 'ad_name': 'Участок, 16.52 сот., ИЖС', 'ad_total_views': 376, 'ad_id': '293667859', 'ad_area': '16,52сот.', 'ad_total_price': 4956000.0, 'ad_address': 'Калужское шоссе \nМосква, ТАО (Троицкий), Вороновское поселение, д. Юрьевка', 'ad_type_company': 'Застройщик', 'ad_phone': '+7 967 209-09-70', 'ad_link': 'https://www.cian.ru/sale/suburban/293667859/', 'ad_date_created': '3 ноя, 18:31', 'electric': 'Есть', 'gaz': 'Есть', 'water': 'Есть', 'sewarage': 'Не указано'},
            #     {'parse_timestamp': str(datetime.now()), 'ad_name': 'Участок в элитном поселке', 'ad_total_views': 524, 'ad_id': '294425662', 'ad_area': '8,1сот.', 'ad_total_price': 6000000.0, 'ad_address': 'Киевское шоссе \nБекасово I \nМосква, ТАО (Троицкий), Новофедоровское поселение, д. Архангельское, улица Барятинская, 27', 'ad_type_company': '', 'ad_phone': '+7 985 632-85-50', 'ad_link': 'https://www.cian.ru/sale/suburban/294425662/', 'ad_date_created': '30 ноя, 12:54', 'electric': 'Есть', 'gaz': 'Магистральный по границе', 'water': 'Центральное', 'sewarage': 'Центральная'},
            #     {'parse_timestamp': str(datetime.now()), 'ad_name': 'Участок, 10.59 сот., ИЖС', 'ad_total_views': 19, 'ad_id': '293667862', 'ad_area': '10,59сот.', 'ad_total_price': 5295000.0, 'ad_address': 'Калужское шоссе \nМосква, ТАО (Троицкий), Вороновское поселение, д. Юрьевка', 'ad_type_company': 'Застройщик', 'ad_phone': '+7 967 209-09-70', 'ad_link': 'https://www.cian.ru/sale/suburban/293667862/', 'ad_date_created': '11 окт, 07:56', 'electric': 'Есть', 'gaz': 'Есть', 'water': 'Есть', 'sewarage': 'Не указано'},
            #     {'parse_timestamp': str(datetime.now()), 'ad_name': 'Участок с пропиской в Москве', 'ad_total_views': 3874, 'ad_id': '283149842', 'ad_area': '7,91сот.', 'ad_total_price': 3559500.0, 'ad_address': 'Калужское шоссе \nМосква, ТАО (Троицкий), Михайлово-Ярцевское поселение, Ярцево лайф кп', 'ad_type_company': 'Ук・оф.Представитель', 'ad_phone': '+7 966 062-84-69', 'ad_link': 'https://www.cian.ru/sale/suburban/283149842/', 'ad_date_created': '29 ноя, 10:15', 'electric': 'Есть', 'gaz': 'Нет', 'water': 'Не указано', 'sewarage': 'Не указано'},
            #     {'parse_timestamp': str(datetime.now()), 'ad_name': 'Участок, 8.85 сот.', 'ad_total_views': 3, 'ad_id': '295560882', 'ad_area': '8,85сот.', 'ad_total_price': 5310000.0, 'ad_address': 'Боровское шоссе \nРассудово \nМосква, ТАО (Троицкий), Новофедоровское поселение, Фаворит кп', 'ad_type_company': 'Застройщик', 'ad_phone': '+7 905 719-68-72', 'ad_link': 'https://www.cian.ru/sale/suburban/295560882/', 'ad_date_created': '1 дек, 13:51', 'electric': 'Есть', 'gaz': 'Не указано', 'water': 'Есть', 'sewarage': 'Есть'},
            #     {'parse_timestamp': str(datetime.now()), 'ad_name': 'Дача около Троицка, 200м от пруда', 'ad_total_views': 540, 'ad_id': '295047506', 'ad_area': '6сот.', 'ad_total_price': 4200000.0, 'ad_address': 'Калужское шоссе \nОльховая \nМосква, ТАО (Троицкий), м. Ольховая, Краснопахорское поселение, № 233 кв-л', 'ad_type_company': 'Агентство недвижимости', 'ad_phone': '+7 964 782-20-28', 'ad_link': 'https://www.cian.ru/sale/suburban/295047506/', 'ad_date_created': '1 дек, 17:05', 'electric': 'Есть', 'gaz': 'Есть', 'water': 'Есть', 'sewarage': 'Не указано'},
            #     {'parse_timestamp': str(datetime.now()), 'ad_name': 'Участок, 12.1 сот., ИЖС', 'ad_total_views': 77, 'ad_id': '292320281', 'ad_area': '12,1сот.', 'ad_total_price': 6050000.0, 'ad_address': 'Калужское шоссе \nМосква, ТАО (Троицкий), Вороновское поселение, д. Юрьевка', 'ad_type_company': 'Застройщик', 'ad_phone': '+7 967 209-09-70', 'ad_link': 'https://www.cian.ru/sale/suburban/292320281/', 'ad_date_created': '3 ноя, 07:47', 'electric': 'Есть', 'gaz': 'Есть', 'water': 'Есть', 'sewarage': 'Не указано'},
            #     {'parse_timestamp': str(datetime.now()), 'ad_name': 'Суперучасток по  суперцене Москва', 'ad_total_views': 3663, 'ad_id': '273294100', 'ad_area': '8сот.', 'ad_total_price': 6499999.0, 'ad_address': 'Калужское шоссе \nМосква, ТАО (Троицкий), Краснопахорское поселение, Лисья горка кп', 'ad_type_company': 'Риелтор', 'ad_phone': '+7 909 980-89-97', 'ad_link': 'https://www.cian.ru/sale/suburban/273294100/', 'ad_date_created': '1 дек, 09:01', 'electric': 'Есть', 'gaz': 'Нет', 'water': 'Есть', 'sewarage': 'Нет'},
            #     {'parse_timestamp': str(datetime.now()), 'ad_name': 'Участок, 11.96 сот.', 'ad_total_views': 31, 'ad_id': '295039891', 'ad_area': '11,96сот.', 'ad_total_price': 6500000.0, 'ad_address': 'Боровское шоссе \nРассудово \nМосква, ТАО (Троицкий), Новофедоровское поселение, Фаворит кп', 'ad_type_company': 'Застройщик', 'ad_phone': '+7 905 719-68-72', 'ad_link': 'https://www.cian.ru/sale/suburban/295039891/', 'ad_date_created': '1 дек, 13:51', 'electric': 'Есть', 'gaz': 'Не указано', 'water': 'Есть', 'sewarage': 'Есть'},
            #     {'parse_timestamp': str(datetime.now()), 'ad_name': 'Участок, 11 сот., ИЖС', 'ad_total_views': 114, 'ad_id': '295410311', 'ad_area': '11сот.', 'ad_total_price': 6500000.0, 'ad_address': 'Калужское шоссе \nПрокшино \nМосква, ТАО (Троицкий), м. Прокшино, Краснопахорское поселение, д. Подосинки, 63', 'ad_type_company': 'Агентство недвижимости', 'ad_phone': '+7 916 603-46-48', 'ad_link': 'https://www.cian.ru/sale/suburban/295410311/', 'ad_date_created': '27 ноя, 16:18', 'electric': 'Есть', 'gaz': 'Нет', 'water': 'Не указано', 'sewarage': 'Нет'},
            #     {'parse_timestamp': str(datetime.now()), 'ad_name': 'Участок, 14.44 сот., ИЖС', 'ad_total_views': 60, 'ad_id': '295285552', 'ad_area': '14,44сот.', 'ad_total_price': 6884000.0, 'ad_address': 'Киевское шоссе \nМосква, ТАО (Троицкий), Михайлово-Ярцевское поселение, Ярцево лайф кп', 'ad_type_company': 'Застройщик', 'ad_phone': '+7 962 363-97-64', 'ad_link': 'https://www.cian.ru/sale/suburban/295285552/', 'ad_date_created': '21 ноя, 07:38', 'electric': 'Не указано', 'gaz': 'Не указано', 'water': 'Есть', 'sewarage': 'Есть'},
            #     {'parse_timestamp': str(datetime.now()), 'ad_name': 'Участок в новом квартале', 'ad_total_views': 341, 'ad_id': '294045602', 'ad_area': '15,36сот.', 'ad_total_price': 69120000.0, 'ad_address': 'Новорижское шоссе \nНахабино \nМосковская область, Истра городской округ, Миллениум Парк кп', 'ad_type_company': 'Агентство недвижимости', 'ad_phone': '+7 903 123-34-06', 'ad_link': 'https://istra.cian.ru/sale/suburban/294045602/', 'ad_date_created': '24 ноя, 10:32', 'electric': 'Нет', 'gaz': 'Нет', 'water': 'Не указано', 'sewarage': 'Нет'},
            #     {'parse_timestamp': str(datetime.now()), 'ad_name': 'Участок, 15.28 сот.', 'ad_total_views': 152, 'ad_id': '293088118', 'ad_area': '15,28сот.', 'ad_total_price': 6876000.0, 'ad_address': 'Новорижское шоссе \nНовоиерусалимская \nМосковская область, Истра городской округ, Эсквайр Парк кп', 'ad_type_company': 'Застройщик', 'ad_phone': '+7 985 432-42-66', 'ad_link': 'https://istra.cian.ru/sale/suburban/293088118/', 'ad_date_created': 'сегодня, 04:04', 'electric': 'Есть', 'gaz': 'Есть', 'water': 'Есть', 'sewarage': 'Есть'},
            #     {'parse_timestamp': str(datetime.now()), 'ad_name': 'Участок в новом квартале', 'ad_total_views': 658, 'ad_id': '292475726', 'ad_area': '14,41сот.', 'ad_total_price': 64845000.0, 'ad_address': 'Новорижское шоссе \nНахабино \nМосковская область, Истра городской округ, Миллениум Парк кп, 8-011', 'ad_type_company': 'Агентство недвижимости', 'ad_phone': '+7 903 123-34-06', 'ad_link': 'https://istra.cian.ru/sale/suburban/292475726/', 'ad_date_created': '24 ноя, 10:32', 'electric': 'Нет', 'gaz': 'Нет', 'water': 'Не указано', 'sewarage': 'Нет'},
            #     {'parse_timestamp': str(datetime.now()), 'ad_name': 'Участок, 11.05 сот.', 'ad_total_views': 12, 'ad_id': '293953553', 'ad_area': '11,05сот.', 'ad_total_price': 788000.0, 'ad_address': 'Калужское шоссе \nМосковская область, Серпухов городской округ, д. Верхнее Шахлово', 'ad_type_company': 'Застройщик', 'ad_phone': '+7 965 290-57-81', 'ad_link': 'https://serpukhov.cian.ru/sale/suburban/293953553/', 'ad_date_created': '10 ноя, 12:16', 'electric': 'Есть', 'gaz': 'Не указано', 'water': 'Не указано', 'sewarage': 'Не указано'},
            #     {'parse_timestamp': str(datetime.now()), 'ad_name': 'Участок в новом квартале', 'ad_total_views': 709, 'ad_id': '294045598', 'ad_area': '13,03сот.', 'ad_total_price': 58635000.0, 'ad_address': 'Новорижское шоссе \nНахабино \nМосковская область, Истра городской округ, Миллениум Парк кп', 'ad_type_company': 'Агентство недвижимости', 'ad_phone': '+7 903 123-34-06', 'ad_link': 'https://istra.cian.ru/sale/suburban/294045598/', 'ad_date_created': '24 ноя, 10:32', 'electric': 'Нет', 'gaz': 'Нет', 'water': 'Не указано', 'sewarage': 'Нет'},
            #     {'parse_timestamp': str(datetime.now()), 'ad_name': 'Участок, 16.97 сот., ИЖС', 'ad_total_views': 2238, 'ad_id': '257141508', 'ad_area': '16,97сот.', 'ad_total_price': 11400000.0, 'ad_address': 'Дмитровское шоссе \nТайнинская \nМосковская область, Мытищи, мкр. 2, 3', 'ad_type_company': 'Застройщик', 'ad_phone': '+7 985 543-95-95', 'ad_link': 'https://mytishchi.cian.ru/sale/suburban/257141508/', 'ad_date_created': '30 ноя, 00:48', 'electric': 'Есть', 'gaz': 'Есть', 'water': 'Есть', 'sewarage': 'Есть'},
            #     {'parse_timestamp': str(datetime.now()), 'ad_name': 'Участок рядом с рекой Истра', 'ad_total_views': 93, 'ad_id': '295283589', 'ad_area': '1230сот.', 'ad_total_price': 123000000.0, 'ad_address': 'Волоколамское шоссе \nНовоиерусалимская \nМосковская область, Истра городской округ, д. Михайловка', 'ad_type_company': 'Агентство недвижимости', 'ad_phone': '+7 903 123-34-06', 'ad_link': 'https://istra.cian.ru/sale/suburban/295283589/', 'ad_date_created': '24 ноя, 10:46', 'electric': 'Нет', 'gaz': 'Нет', 'water': 'Не указано', 'sewarage': 'Нет'},
            #     {'parse_timestamp': str(datetime.now()), 'ad_name': 'Участок, 8.3 сот.', 'ad_total_views': 52, 'ad_id': '295408712', 'ad_area': '8,3сот.', 'ad_total_price': 9750000.0, 'ad_address': 'Рублево-Успенское шоссе \nЗвенигород \nМосковская область, Одинцовский городской округ, д. Палицы, улица Массив 1', 'ad_type_company': 'Застройщик', 'ad_phone': '+7 966 047-01-64', 'ad_link': 'https://odintsovo.cian.ru/sale/suburban/295408712/', 'ad_date_created': '30 ноя, 01:40', 'electric': 'Есть', 'gaz': 'Есть', 'water': 'Есть', 'sewarage': 'Есть'},
            #     {'parse_timestamp': str(datetime.now()), 'ad_name': 'Участок, 6.5 сот., ИЖС', 'ad_total_views': 311, 'ad_id': '285953078', 'ad_area': '6,5сот.', 'ad_total_price': 7400000.0, 'ad_address': 'Новорижское шоссе \nМанихино I \nМосковская область, Истра городской округ, д. Покровское, бульвар Новорижский', 'ad_type_company': 'Риелтор', 'ad_phone': '+7 964 785-73-71', 'ad_link': 'https://istra.cian.ru/sale/suburban/285953078/', 'ad_date_created': 'вчера, 16:32', 'electric': 'Есть', 'gaz': 'Магистральный по границе', 'water': 'Центральное', 'sewarage': 'Септик'},
            #     {'parse_timestamp': str(datetime.now()), 'ad_name': 'Участок, 11.26 сот.', 'ad_total_views': 59, 'ad_id': '293880666', 'ad_area': '11,26сот.', 'ad_total_price': 1013400.0, 'ad_address': 'Калужское шоссе \nМосковская область, Чехов городской округ, с. Шарапово', 'ad_type_company': 'Застройщик', 'ad_phone': '+7 905 733-60-23', 'ad_link': 'https://chekhov.cian.ru/sale/suburban/293880666/', 'ad_date_created': '30 ноя, 00:56', 'electric': 'Есть', 'gaz': 'Не указано', 'water': 'Не указано', 'sewarage': 'Не указано'},
            #     {'parse_timestamp': str(datetime.now()), 'ad_name': 'Участок, 40 сот.', 'ad_total_views': 276, 'ad_id': '292673567', 'ad_area': '40сот.', 'ad_total_price': 359047599.0, 'ad_address': 'Рублево-Успенское шоссе \nКрасногорская \nМосковская область, Красногорск городской округ, Ильинские Дачи СНТ, улица 4-я Архангельская', 'ad_type_company': 'Агентство недвижимости', 'ad_phone': '+7 966 153-69-63', 'ad_link': 'https://krasnogorsk.cian.ru/sale/suburban/292673567/', 'ad_date_created': '29 ноя, 17:28', 'electric': 'Есть', 'gaz': 'Есть', 'water': 'Не указано', 'sewarage': 'Не указано'},
            #     {'parse_timestamp': str(datetime.now()), 'ad_name': 'Участок, 6 сот.', 'ad_total_views': 22, 'ad_id': '295408705', 'ad_area': '6сот.', 'ad_total_price': 6970000.0, 'ad_address': 'Рублево-Успенское шоссе \nЗвенигород \nМосковская область, Одинцовский городской округ, д. Палицы, улица Массив 1', 'ad_type_company': 'Застройщик', 'ad_phone': '+7 966 047-01-64', 'ad_link': 'https://odintsovo.cian.ru/sale/suburban/295408705/', 'ad_date_created': '30 ноя, 01:40', 'electric': 'Есть', 'gaz': 'Есть', 'water': 'Есть', 'sewarage': 'Есть'},
            #     {'parse_timestamp': str(datetime.now()), 'ad_name': 'Участок, 3200 сот., ИЖС', 'ad_total_views': 425, 'ad_id': '293259736', 'ad_area': '3200сот.', 'ad_total_price': 574476159.0, 'ad_address': 'Рублево-Успенское шоссе \nРаздоры \nМосковская область, Одинцовский городской округ, д. Шульгино, улица Полевая', 'ad_type_company': 'Агентство недвижимости', 'ad_phone': '+7 916 147-15-24', 'ad_link': 'https://odintsovo.cian.ru/sale/suburban/293259736/', 'ad_date_created': 'сегодня, 09:16', 'electric': 'Есть', 'gaz': 'Есть', 'water': 'Есть', 'sewarage': 'Есть'},
            #     {'parse_timestamp': str(datetime.now()), 'ad_name': 'Участок, 8 сот.', 'ad_total_views': 90, 'ad_id': '270634360', 'ad_area': '8сот.', 'ad_total_price': 1440000.0, 'ad_address': 'Волоколамское шоссе \nРумянцево \nМосковская область, Истра городской округ, Леоново кп, 67', 'ad_type_company': 'Застройщик', 'ad_phone': '+7 967 293-96-92', 'ad_link': 'https://istra.cian.ru/sale/suburban/270634360/', 'ad_date_created': '17 ноя, 08:02', 'electric': 'Есть', 'gaz': 'Есть', 'water': 'Есть', 'sewarage': 'Есть'},
            #     {'parse_timestamp': str(datetime.now()), 'ad_name': 'Участок, 100 сот., ИЖС', 'ad_total_views': 201, 'ad_id': '289779652', 'ad_area': '100сот.', 'ad_total_price': 170000000.0, 'ad_address': 'Новорижское шоссе \nЗвенигород \nМосковская область, Одинцовский городской округ, Мэдисон Парк кп, 94', 'ad_type_company': 'Агентство недвижимости', 'ad_phone': '+7 915 162-52-04', 'ad_link': 'https://odintsovo.cian.ru/sale/suburban/289779652/', 'ad_date_created': 'сегодня, 09:13', 'electric': 'Есть', 'gaz': 'Есть', 'water': 'Есть', 'sewarage': 'Есть'},
            #     {'parse_timestamp': str(datetime.now()), 'ad_name': 'Участок, 14.6 сот.', 'ad_total_views': 203, 'ad_id': '240387358', 'ad_area': '14,6сот.', 'ad_total_price': 2774000.0, 'ad_address': 'Волоколамское шоссе \nМосковская область, Истра городской округ, Куртниково кп', 'ad_type_company': 'Застройщик', 'ad_phone': '+7 967 263-67-79', 'ad_link': 'https://istra.cian.ru/sale/suburban/240387358/', 'ad_date_created': '27 сен, 07:41', 'electric': 'Есть', 'gaz': 'Есть', 'water': 'Не указано', 'sewarage': 'Есть'},
            #     {'parse_timestamp': str(datetime.now()), 'ad_name': 'Участок, 6 сот., ДНП', 'ad_total_views': 1151, 'ad_id': '289853456', 'ad_area': '6сот.', 'ad_total_price': 300000.0, 'ad_address': 'Новорязанское шоссе \nКузяево \nМосковская область, Раменский городской округ, д. Кузяево', 'ad_type_company': 'Агентство недвижимости', 'ad_phone': '+7 985 360-14-50', 'ad_link': 'https://ramenskoye.cian.ru/sale/suburban/289853456/', 'ad_date_created': '30 ноя, 00:51', 'electric': 'Есть', 'gaz': 'Магистральный по границе', 'water': 'Не указано', 'sewarage': 'Нет'},
            #     {'parse_timestamp': str(datetime.now()), 'ad_name': 'Участок, 25.82 сот., ИЖС', 'ad_total_views': 728, 'ad_id': '291494181', 'ad_area': '25,82сот.', 'ad_total_price': 69538000.0, 'ad_address': 'Рублево-Успенское шоссе \nИльинское \nМосковская область, Красногорск городской округ, пос. Ильинское-Усово, Тен кп', 'ad_type_company': 'Застройщик', 'ad_phone': '+7 985 569-60-73', 'ad_link': 'https://krasnogorsk.cian.ru/sale/suburban/291494181/', 'ad_date_created': 'сегодня, 08:41', 'electric': 'Есть', 'gaz': 'Магистральный по границе', 'water': 'Центральное', 'sewarage': 'Центральная'},
            #     {'parse_timestamp': str(datetime.now()), 'ad_name': 'Участок, 25.93 сот.', 'ad_total_views': 354, 'ad_id': '291989147', 'ad_area': '25,93сот.', 'ad_total_price': 280057127.0, 'ad_address': 'Рублево-Успенское шоссе \nКрасногорская \nМосковская область, Красногорск городской округ, Ильинские Дачи СНТ, улица 4-я Архангельская', 'ad_type_company': 'Агентство недвижимости', 'ad_phone': '+7 967 208-90-73', 'ad_link': 'https://krasnogorsk.cian.ru/sale/suburban/291989147/', 'ad_date_created': '29 ноя, 17:28', 'electric': 'Есть', 'gaz': 'Есть', 'water': 'Не указано', 'sewarage': 'Не указано'},
            #     {'parse_timestamp': str(datetime.now()), 'ad_name': 'Участок, 14.64 сот.', 'ad_total_views': 98, 'ad_id': '285365931', 'ad_area': '14,64сот.', 'ad_total_price': 1933600.0, 'ad_address': 'Симферопольское шоссе \nЛуч \nМосковская область, Чехов городской округ, д. Баранцево, Швейцарская Долина кп', 'ad_type_company': 'Застройщик', 'ad_phone': '+7 964 716-10-31', 'ad_link': 'https://chekhov.cian.ru/sale/suburban/285365931/', 'ad_date_created': '30 ноя, 00:46', 'electric': 'Есть', 'gaz': 'Есть', 'water': 'Не указано', 'sewarage': 'Не указано'},
            #     {'parse_timestamp': str(datetime.now()), 'ad_name': 'Участок, 8 сот., ДНП', 'ad_total_views': 606, 'ad_id': '282359877', 'ad_area': '8сот.', 'ad_total_price': 1440000.0, 'ad_address': 'Волоколамское шоссе \nЗеленоград — Крюково \nИстра \nМосковская область, м.\xa0Зеленоград — Крюково, Истра городской округ, д. Духанино', 'ad_type_company': 'Агентство недвижимости', 'ad_phone': '+7 985 360-14-50', 'ad_link': 'https://istra.cian.ru/sale/suburban/282359877/', 'ad_date_created': '30 ноя, 00:51', 'electric': 'Есть', 'gaz': 'Магистральный по границе', 'water': 'Не указано', 'sewarage': 'Не указано'},
            #     {'parse_timestamp': str(datetime.now()), 'ad_name': 'Участок, 14.81 сот.', 'ad_total_views': 953, 'ad_id': '278578391', 'ad_area': '14,81сот.', 'ad_total_price': 2195259.0, 'ad_address': 'Новорижское шоссе \nДубосеково \nМосковская область, Волоколамский городской округ, Эко Озеро кп, 2', 'ad_type_company': 'Застройщик', 'ad_phone': '+7 965 149-23-24', 'ad_link': 'https://www.cian.ru/sale/suburban/278578391/', 'ad_date_created': 'сегодня, 09:00', 'electric': 'Есть', 'gaz': 'Есть', 'water': 'Есть', 'sewarage': 'Есть'},
            #     {'parse_timestamp': str(datetime.now()), 'ad_name': 'Участок, 21.5 сот., ИЖС', 'ad_total_views': 729, 'ad_id': '291989138', 'ad_area': '21,5сот.', 'ad_total_price': 18500000.0, 'ad_address': 'Киевское шоссе \nАпрелевка \nМосковская область, Наро-Фоминский городской округ, д. Мартемьяново, улица Зеленая, 117', 'ad_type_company': 'Агентство недвижимости', 'ad_phone': '+7 967 208-90-37', 'ad_link': 'https://naro-fominsk.cian.ru/sale/suburban/291989138/', 'ad_date_created': '29 ноя, 17:28', 'electric': 'Есть', 'gaz': 'Есть', 'water': 'Не указано', 'sewarage': 'Не указано'},
            #     {'parse_timestamp': str(datetime.now()), 'ad_name': 'Участок, 11.83 сот.', 'ad_total_views': 52, 'ad_id': '278578321', 'ad_area': '11,83сот.', 'ad_total_price': 2314952.0, 'ad_address': 'Симферопольское шоссе \nСерпухов \nМосковская область, Серпухов городской округ, Петрухино-1 кп', 'ad_type_company': 'Застройщик', 'ad_phone': '+7 966 053-20-56', 'ad_link': 'https://serpukhov.cian.ru/sale/suburban/278578321/', 'ad_date_created': '30 ноя, 01:17', 'electric': 'Не указано', 'gaz': 'Не указано', 'water': 'Не указано', 'sewarage': 'Не указано'},
            #     {'parse_timestamp': str(datetime.now()), 'ad_name': 'Участок, 19.9 сот.', 'ad_total_views': 80, 'ad_id': '291989128', 'ad_area': '19,9сот.', 'ad_total_price': 120000000.0, 'ad_address': 'Новорижское шоссе \nНахабино \nМосковская область, Истра городской округ, д. Чесноково', 'ad_type_company': 'Агентство недвижимости', 'ad_phone': '+7 966 153-69-63', 'ad_link': 'https://istra.cian.ru/sale/suburban/291989128/', 'ad_date_created': '29 ноя, 17:28', 'electric': 'Есть', 'gaz': 'Есть', 'water': 'Не указано', 'sewarage': 'Не указано'},
            #     {'parse_timestamp': str(datetime.now()), 'ad_name': 'Участок, 14.17 сот.', 'ad_total_views': 135, 'ad_id': '290535908', 'ad_area': '14,17сот.', 'ad_total_price': 2852939.0, 'ad_address': 'Симферопольское шоссе \nШарапова Охота \nМосковская область, Серпухов городской округ, Вяземские Сады кп', 'ad_type_company': 'Застройщик', 'ad_phone': '+7 965 109-94-35', 'ad_link': 'https://serpukhov.cian.ru/sale/suburban/290535908/', 'ad_date_created': '10 ноя, 11:51', 'electric': 'Есть', 'gaz': 'Есть', 'water': 'Есть', 'sewarage': 'Есть'},
            #     {'parse_timestamp': str(datetime.now()), 'ad_name': 'Единственный участок в поселке!', 'ad_total_views': 410, 'ad_id': '291989145', 'ad_area': '15сот.', 'ad_total_price': 44800000.0, 'ad_address': 'Новорижское шоссе \nНахабино \nМосковская область, Истра городской округ, д. Веледниково, улица Усадебная', 'ad_type_company': 'Агентство недвижимости', 'ad_phone': '+7 964 568-45-35', 'ad_link': 'https://istra.cian.ru/sale/suburban/291989145/', 'ad_date_created': '29 ноя, 17:28', 'electric': 'Есть', 'gaz': 'Есть', 'water': 'Не указано', 'sewarage': 'Не указано'},
            #     {'parse_timestamp': str(datetime.now()), 'ad_name': 'Участок, 7 сот., ИЖС', 'ad_total_views': 256, 'ad_id': '293386154', 'ad_area': '7сот.', 'ad_total_price': 5595000.0, 'ad_address': 'Волоколамское шоссе \n73 км \nМосковская область, Истра городской округ, Аркадия кп', 'ad_type_company': 'Застройщик', 'ad_phone': '+7 985 055-41-48', 'ad_link': 'https://istra.cian.ru/sale/suburban/293386154/', 'ad_date_created': '4 ноя, 04:05', 'electric': 'Есть', 'gaz': 'Магистральный по границе', 'water': 'Есть', 'sewarage': 'Центральная'}
            # ]


            # write msg about found ads
            # write_execution_logs(f'Found avito - {len(avito_ads)}\nFound cian - {len(cian_ads)}')
            # write_execution_logs(f'Exceptions after parsing and unpacking - {exceptions_msg}')
            logging.info(f'Found avito - {len(avito_ads)}')
            logging.info(f'Found cian - {len(cian_ads)}')
            if exceptions_msg:
                logging.error(f'Exceptions after parsing and unpacking - {exceptions_msg}')
            
            # update prices and views history     
            try:
                update_history_csv(cian_ads, CIAN_HISTORY_CSV_FN)
                update_history_csv(avito_ads, AVITO_HISTORY_CSV_FN)
            except Exception as ex:
                ex_msg = f'\nEXCEPTION WITH UPDATE HISTORY CSV FILES - {ex}\n'
                exceptions_msg += ex_msg
                logging.error(ex_msg)
            else:
                msg = 'History csv for cian and avito was updated!'
                logging.info(msg)
           
            # update total ads
            try:
                update_total_csv(cian_ads, CIAN_TOTAL_CSV_FN)
                update_total_csv(avito_ads, AVITO_TOTAL_CSV_FN)
            except Exception as ex:
                ex_msg = f'\nEXCEPTION WITH UPDATE TOTAL CSV FILES - {ex}\n'
                exceptions_msg += ex_msg
                logging.error(ex_msg)
            else:
                msg = 'Total csv for cian and avito was updated!'
                logging.info(msg)

            # write msg about update total and history
            # write_execution_logs(f'Exceptions after update total and history - {exceptions_msg}')
     
        # send msg about errors
        if exceptions_msg:
            try:
                send_email_errors = send_email_msg(
                    subject_msg=ERROR_NOTIFICATION_SUBJECT, 
                    send_from=MAIL_LOGIN, password=MAIL_PASSWORD,
                    send_to=MAIL_SEND_TO, body_msg=exceptions_msg
                )
            except Exception as ex:
                msg = '\nEXCEPTION WITH SENDING EMAIL MESSAGE!\n'
                logging.info(msg)
            else:
                logging.info('Sending email was completed')
                if send_email_errors:
                    logging.error(str(send_email_errors))
        
        # next program run in the 22:00
        next_time_point = datetime.combine(datetime.now().date(), time(22, 0, 0))
        if next_time_point < datetime.now():
            next_time_point += timedelta(days=1)

        msg = f'Завершение работы парсера, следующий запуск в [{str(next_time_point)}]'
        print(msg)
        logging.info(msg)
        # write_execution_logs(msg)

        # sleep to point 22:00 today or tommorow 
        sleep_to_point(next_time_point)

if __name__ == '__main__':
    main()
