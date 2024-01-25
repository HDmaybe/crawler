import requests
from bs4 import BeautifulSoup as bs
import traceback
import re
import psycopg2

db_params = {
    'host': 'localhost',
    'port': '5432',
    'user': 'postgres',
    'password': '',
    'database': 'postgres'
}

conn = psycopg2.connect(**db_params)
conn.set_session(autocommit=True)
cursor = conn.cursor()

def extract_numbers(input_string):
    return re.sub('\D', '',input_string)

def check_item(item_id):
    cursor.execute(f"select * from baon.items where pid = '{item_id}' ")
    row = cursor.fetchall()
    return row

dex = 1

# base_url : ?page= 중요하네..
base_url = "https://ba-on.com"
headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}

response1 = requests.get(base_url, headers=headers)
soup1 = bs(response1.text, "html.parser")

category_list =soup1.select('div.Menu_list ul li a')
allow_categorys = ['OUTER','TOP','PANTS', 'SKIRT', 'DRESS', 'ACC']

for category in category_list:
    category_lv1 = category.text
    if category_lv1 not in allow_categorys:
        continue

    url2 = base_url + category['href']
    response2 = requests.get(url2, headers=headers)
    soup2 = bs(response2.text, "html.parser")
    category_lv2s = soup2.select('ul.menuCategory li a')
    for category_lv2 in category_lv2s:
        base_url_cat2 = base_url + category_lv2['href']
        response_instance = requests.get(base_url_cat2 + "?page=1",headers=headers)
        soup4 = bs(response_instance.text, "html.parser")
        final_page_tag = soup4.select_one('.last')['href']        
        
        if final_page_tag == "#none":
            iteration = 1
        else:
            iteration = final_page_tag.split("=")[-1]
        
        for page_no in range(1, int(iteration)+1 ):
            item_list_url = base_url_cat2 +  f"?page={page_no}"
            response = requests.get(item_list_url, headers=headers)
            soup3 = bs(response.text, "html.parser")
            item_list = soup3.select('div.xans-product-normalpackage li.xans-record-')
            if item_list is not None:
                try:
                    for item in item_list:

                        # 1. 아이디
                        product_id = item['id'].split('_')[-1]
                        if check_item(product_id) != []:
                            continue

                        # 2. 가격
                        price_tag = item.select_one('.sale.PointColor')
                        second_price_text = price_tag.select_one('s').get_text(strip=True)
                        price = extract_numbers(second_price_text)+"원"
                        
                        # 3. 이름
                        name = item.select_one('li.name span').get_text(strip=True)

                        #6. 할인가
                        price_tag.s.decompose()
                        second_sele_text = price_tag.get_text(strip=True)
                        sale_price = extract_numbers(second_sele_text)
                        sale_price = sale_price+'원' if sale_price != '' else ''
                        
                        thumbnail_tag = item.select_one('div.thumbnail p.prdImg')

                        # 4. 링크
                        href = base_url + thumbnail_tag.select_one('a')['href']

                        # 5. 이미지 링크
                        img_src = base_url + thumbnail_tag.select_one('img')['src']
                        insert_query = """
                        INSERT INTO baon.items (pid, category1, category2, url, product, price, sale, img) 
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"""
                        data = (product_id, category_lv1, category_lv2.get_text().split()[0], href, name, price, sale_price, img_src)
                        cursor.execute(insert_query, data)
                
                except Exception as e:
                    print(traceback.format_exc())
            else:
                break
