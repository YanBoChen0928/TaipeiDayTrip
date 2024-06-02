import fastapi
import json
import mysql.connector
import re

# 假設 JSON 數據存儲在文件中
json_file = 'data/taipei-attractions.json'

# 讀取 JSON 數據
with open(json_file, 'r', encoding='utf-8') as file:
    data = json.load(file)

# 要記得處理一些 null，因為有兩筆資料的的 mrt 為none, 轉成空的字符串，不然在app.py使用pydantic(mrt:str)會有問題
for result in data['result']['results']:
    if result['MRT'] is None:
        result['MRT'] = ''

with mysql.connector.connect(
        host='localhost',
        user='wehelp',
        password='wehelp',
        database='TaipeiDayTrip_db'
    ) as cnx:
    with cnx.cursor() as cursor:

        try:
            # 連接到 MySQL 數據庫

                    # 獲取景點數據
                    attractions = data['result']['results']

                    for attraction in attractions:
                        id = attraction.get('_id')
                        name = attraction.get('name')
                        category = attraction.get('CAT')
                        description = attraction.get('description')
                        address = attraction.get('address')
                        transport = attraction.get('direction')
                        mrt = attraction.get('MRT')
                        lat = attraction.get('latitude')
                        lng = attraction.get('longitude')

                        # 查詢數據庫檢查是否已存在相同 id 的景點
                        cursor.execute("SELECT id FROM attractions WHERE id = %s", (id,))
                        existing_attraction = cursor.fetchone()

                        if not existing_attraction:
                            # 插入景點信息 (attractions 資料表)
                            sql = """
                                INSERT INTO attractions (id, name, category, description, address, transport, mrt, lat, lng) 
                                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                            """
                            values = (id, name, category, description, address, transport, mrt, lat, lng)
                            cursor.execute(sql, values)

                            # 插入圖片信息
                            if 'file' in attraction:
                                image_urls = attraction['file'].split('http')
                                for image_url in image_urls:
                                    # 確保 image_url 是字符串
                                    if isinstance(image_url, str):
                                        image_url = 'http' + image_url.strip()
                                        if re.search(r'\.(jpg|jpeg|png)$', image_url, re.IGNORECASE):
                                            sql_image = """
                                                INSERT INTO images (attraction_id, image_url) VALUES (%s, %s)
                                            """
                                            values_image = (id, image_url)
                                            cursor.execute(sql_image, values_image)

                            
                    # 提交事務
                    cnx.commit()

        except mysql.connector.Error as err:
            print(f"Error: {err}")
            cnx.rollback()
        finally:
            if cursor:
                cursor.close()
            if cnx:
                cnx.close()