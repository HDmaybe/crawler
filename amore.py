import requests
import json
import psycopg2
from tqdm import tqdm


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


def check_item(item_id):
    cursor.execute(f"select * from baon.items where pid = '{item_id}' ")
    row = cursor.fetchall()
    return row

headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}

Category = {97: "스킨케어", 98: "메이크업", 99: "향수", 100: "생활용품" , 101: "소품&도구" , 102: "뷰티푸드" , 103: "남성" , 104: "베이비"}
for key, value in Category.items():
    req = requests.get(f"https://api-gw.amoremall.com/display/v2/M01/online-products/by-category?categorySn={key}&containsFilter=true&limit=40&offset=0&sortType=Ranking", headers = headers)
    item_count = json.loads(req.text)["totalCount"]
    group_num  = item_count//40
    print(group_num)
    print("한카테고리 시작")
    for i in tqdm(range(0, (group_num+1)*40, 40)):
        print(i)
        req_item = requests.get(f"https://api-gw.amoremall.com/display/v2/M01/online-products/by-category?categorySn={key}&containsFilter=true&limit=40&offset={i}&sortType=Ranking", headers = headers)
        data = json.loads(req_item.text)['products']
        for j in range(len(data)):

            # 1. 아이디 s
            product_id = data[j]['onlineProdCode']
            if check_item(product_id) != []:
                continue
            
            # 2. 이름
            name = data[j]['onlineProdName'] 

            # 3. 가격
            price = str(data[j]['standardPrice']) + '원'
            
            #4. 할인가
            sale_price = str(data[j]['discountedPrice']) + '원'

            # 5. 링크
            onlineProdSn = data[j]['onlineProdSn']
            href = f"https://www.amoremall.com/kr/ko/product/detail?onlineProdSn={onlineProdSn}&onlineProdCode={product_id}"

            # 6. 이미지 링크
            img_src = data[j]['imgUrl']

            # 7. 브랜드
            brand = data[j]['brandName']

            # 8. 카테고리 = value
            insert_query = """
            INSERT INTO amore.items (pid, product, category, brand, price, sale, url, img) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"""
            each_item = (product_id, name, value, brand, price, sale_price, href,img_src)
            cursor.execute(insert_query, each_item)





# req2 = requests.get("https://api-gw.amoremall.com/display/v2/M01/online-products/by-category?categorySn=97&containsFilter=false&limit=40&offset=120&sortType=Ranking")
# req3 = requests.get("https://api-gw.amoremall.com/display/v2/M01/online-products/by-category?categorySn=98&containsFilter=true&limit=40&offset=0&sortType=Ranking")
# data = json.loads(req2.text)

# print(type(data['products']))