import requests
from bs4 import BeautifulSoup as bs
import psycopg2

conn = psycopg2.connect(
    host="localhost",
    database="postgres",
    user="postgres",
    port="5432"
)

cursor = conn.cursor()

for page_number in range(1,6):
    url = f"https://ba-on.com/category/%ED%8C%A8%EB%94%A9/83/&page={page_number}"
    response = requests.get(url)
    if response.status_code == 200:
        html = response.text
        soup = bs(html, 'html.parser')
        product_ids = [id.get('id') for id in soup.select('.prdList > li')]
        cat1 = '아우터'
        cat2 = '패딩'
        product_links = [link.get('href') for link in soup.select('.name > a')]
        product_names = [name.text.strip() for name in soup.select('.name > a > span')]
        product_prices = [price.text.strip() for price in soup.select('.price')]
        product_sale_prices = [sale_price.text.strip() for sale_price in soup.select('.sale')]
        product_images = [img.get('src') for img in soup.select('.thumb > img')]
        for i in range(len(product_ids)):
            print(product_ids[i])
            cursor.execute("""
                INSERT INTO baon.items (pid, category1, category2, url, product, price, sale, img)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (product_ids[i], cat1, cat2, product_names[i], product_links[i], product_prices[i], product_sale_prices[i], product_images[i]))

        conn.commit()


cursor.close()
conn.close()
