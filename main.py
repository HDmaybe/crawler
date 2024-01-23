import requests
from bs4 import BeautifulSoup as bs


import psycopg2

# PostgreSQL 연결 정보
db_params = {
    'host': 'localhost',
    'port': '5432',
    'user': 'postgres',
    'password': '',
    'database': 'postgres'
}

def extract_numbers(input_string):
    return ''.join(char for char in input_string if char.isdigit())

base_url = "https://ba-on.com/category/%EA%B0%80%EB%94%94%EA%B1%B4/62/?page="



for i in range(1,9):
    url = base_url + str(i)
    response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
    if response.status_code == 200:
        soup = bs(response.text, "html.parser")

        try:
            
            conn = psycopg2.connect(**db_params)
            cursor = conn.cursor()

            # 1. 아이디
            product_ids = [anchor_box['id'].split('_')[-1] for anchor_box in soup.select('div.xans-product-normalpackage li[id^="anchorBoxId_"]')]

            # 2. 가격
            prices = []
            for price_tag in soup.select('div.xans-product-normalpackage li.price'):
                second_price_text = price_tag.select_one('p:nth-of-type(2) s').get_text(strip=True)
                prices.append(extract_numbers(second_price_text)+"원")

            # 3. 이름
            names = [name_span.get_text(strip=True) for name_span in soup.select('div.xans-product-normalpackage li.name span')]

            # 4. 링크
            hrefs = [a_tag['href'] for a_tag in soup.select('div.xans-product-normalpackage div.thumbnail p.prdImg a')]
            
            # 5. 이미지 링크
            img_srcs = [img_tag['src'] for img_tag in soup.select('div.xans-product-normalpackage div.thumbnail p.prdImg a img')]
            
            #6. 할인가
            sale_prices = []
            for sale_price_tag in soup.select('div.xans-product-normalpackage .price p.sale.PointColor'):
                sale_price_1 = sale_price_tag.text
                result = extract_numbers(sale_price_1)
                if int(result)>200000:
                    sale_prices.append(result[-5:]+"원")
                else:
                    sale_prices.append("없음")
                
            #7. 카테1    
            category1 = "아우터"
            #8. 카테2
            category2 = "가디건"

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
        print(f"status code:  {response.status_code}")
