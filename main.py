import requests
from bs4 import BeautifulSoup as bs
import math
import psycopg2

db_params = {
    'host': 'localhost',
    'port': '5432',
    'user': 'postgres',
    'password': '',
    'database': 'postgres'
}

def extract_numbers(input_string):
    return ''.join(char for char in input_string if char.isdigit())

# base_url : ?page= 중요하네..
base_url = "https://ba-on.com/index.html"
response1 = requests.get(base_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10 )
soup1 = bs(response1.text, "html.parser")
selected_li_tags = soup1.select('div.Menu_list ul li')[8:13]
href_list = [li.a for li in selected_li_tags]
category11s = [li.a.get_text() for li in selected_li_tags]
allow_categorys = ['OUTRE']
for allow_category in href_list:
    if allow_category.text not in allow_categorys:
        continue
    url2 = "https://ba-on.com" + allow_category['href']
    response2 = requests.get(url2, headers={"User-Agent": "Mozilla/5.0"} , timeout=10)
    soup2 = bs(response2.text, "html.parser")
    selected_a_tags = soup2.select('ul.menuCategory li a')
    href_list2= [a['href'] for a in selected_a_tags]
    category22s = [a.get_text() for a in selected_a_tags]

    for b in range(len(category22s)):
        base_url_cat2 = "https://ba-on.com" + href_list2[b] +"?page="
        for j in range(1, 40):
            new_url = base_url_cat2 + str(j)
            response = requests.get(new_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
            if response.status_code == 200:
                soup3 = bs(response.text, "html.parser")
                try:
                    conn = psycopg2.connect(**db_params)
                    cursor = conn.cursor()
                    
                    # 1. 아이디
                    product_ids = [anchor_box['id'].split('_')[-1] for anchor_box in soup3.select('div.xans-product-normalpackage li[id^="anchorBoxId_"]')]
                    
                    # 2. 가격
                    prices = []
                    for price_tag in soup3.select('div.xans-product-normalpackage li.price'):
                        second_price_text = price_tag.select_one('p:nth-of-type(2) s').get_text(strip=True)
                        prices.append(extract_numbers(second_price_text)+"원")

                    # 3. 이름
                    names = [name_span.get_text(strip=True) for name_span in soup3.select('div.xans-product-normalpackage li.name span')]

                    # 4. 링크
                    hrefs = [a_tag['href'] for a_tag in soup3.select('div.xans-product-normalpackage div.thumbnail p.prdImg a')]
                    
                    # 5. 이미지 링크
                    img_srcs = [img_tag['src'] for img_tag in soup3.select('div.xans-product-normalpackage div.thumbnail p.prdImg a img')]
                    
                    #6. 할인가
                    sale_prices = []
                    for sale_price_tag in soup3.select('div.xans-product-normalpackage .price p.sale.PointColor'):
                        sale_price_1 = sale_price_tag.text
                        result = extract_numbers(sale_price_1)
                        if int(result)>200000:
                            if math.log10(int(result))>=11:
                                sale_prices.append(result[-6:]+"원")
                            else:
                                sale_prices.append(result[-5:]+"원")
                        else:
                            sale_prices.append("없음")
                        
                    #7. 카테1    
                    category1 = allow_category.text
                    #8. 카테2
                    category2 = category22s[b]


                    for product_id, href, price, name, img_src, sale_price in zip(product_ids, hrefs, prices, names, img_srcs, sale_prices):
                        insert_query = """
                        INSERT INTO baon.items (pid, category1, category2, url, product, price, sale, img) 
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"""
                        data = (product_id, category1, category2, f"ba-on.com{href}", name, price, sale_price, img_src )
                        cursor.execute(insert_query, data)

                    conn.commit()
                except Exception as e:
                    print(f"에러1: {e}")
            else:
                break









