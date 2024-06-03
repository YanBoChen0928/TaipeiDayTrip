from fastapi import *
from fastapi.responses import FileResponse, JSONResponse
app=FastAPI()

from fastapi import FastAPI, Query, HTTPException
from pydantic import BaseModel
from typing import Optional
import mysql.connector
from mysql.connector import Error

# Static Pages (Never Modify Code in this Block)
@app.get("/", include_in_schema=False)
async def index(request: Request):
	return FileResponse("./static/index.html", media_type="text/html")
@app.get("/attraction/{id}", include_in_schema=False)
async def attraction(request: Request, id: int):
	return FileResponse("./static/attraction.html", media_type="text/html")
@app.get("/booking", include_in_schema=False)
async def booking(request: Request):
	return FileResponse("./static/booking.html", media_type="text/html")
@app.get("/thankyou", include_in_schema=False)
async def thankyou(request: Request):
	return FileResponse("./static/thankyou.html", media_type="text/html")


mysql_config = {
    'host': 'localhost',
    'user': 'wehelp',
    'password': 'wehelp',
    'database': 'TaipeiDayTrip_db'
}
class Attraction(BaseModel):
    id: int
    name: str
    category: str
    description: str
    address: str
    transport: str
    mrt: str
    lat: float
    lng: float
    images: Optional[list[str]]

class ResponseAttractions(BaseModel):
    nextPage: Optional[int] = None
    data: list[Attraction]

class ResponseAttractionId(BaseModel):
    data: Attraction #只有單一、上面那個是多個，所以是list


def get_db_connection():
    try:
        return mysql.connector.connect(**mysql_config)
      
    except Error as e:
        print(f"Error connecting to MySQL Platform: {e}")
        raise HTTPException(status_code=500, detail="伺服器內部錯誤")

#API: Attractions
@app.get("/api/attractions", response_model=ResponseAttractions)
def get_attractions(
    page: int = Query(0, ge=0), #ge: greater than or equal to" 的縮寫
    keyword: str = Query(None)
):
    limit = 12
    offset = page * limit
    query = "SELECT * FROM attractions WHERE 1=1"
    params = []

    if keyword:
        query += " AND (name LIKE %s OR mrt = %s)"
        params.append(f"%{keyword}%")
        params.append(keyword)
    
    query += " LIMIT %s OFFSET %s"
    params.append(limit)
    params.append(offset)
    
    try:
        cnx = get_db_connection()
        cursor = cnx.cursor(dictionary=True, buffered=True)
        # Execute the main query
        cursor.execute(query, params)
        attractions = cursor.fetchall()
        # Fetch and attach images to each attraction
        for attraction in attractions:
            cursor.execute("SELECT image_url FROM images WHERE attraction_id = %s", (attraction['id'],))
            images = cursor.fetchall()
            attraction['images'] = [image['image_url'] for image in images]
        # Check if there is a next page
        cursor.execute("SELECT COUNT(*) as total FROM attractions WHERE 1=1")
        if keyword:
            cursor.execute("SELECT COUNT(*) as total FROM attractions WHERE name LIKE %s OR mrt = %s", (f"%{keyword}%", keyword))
        total_attractions = cursor.fetchone()['total']

        nextPage = page + 1 if (offset + limit) < total_attractions else None
    
    except Error as e:
        print(f"Error connecting to API/Attractions: {e}")
        raise HTTPException(status_code=500, detail="伺服器內部錯誤")
    finally:
        cursor.close()
        cnx.close()
    #有時候位子對，但是顯示錯誤，主要是因為 tab 跟空格
        return {"nextPage": nextPage, "data": attractions}


#Attraction_id API （還有bug要處理）
@app.get("/api/attraction/{attraction_id}") #response_model=ResponseAttractionId
def get_attraction(attraction_id: int):
  try:
    cnx = get_db_connection()
    cursor = cnx.cursor(dictionary=True, buffered=True)
    cursor.execute("SELECT * FROM attractions WHERE id = %s", (attraction_id,))
    attraction = cursor.fetchone()

    if not attraction:
        raise HTTPException(status_code=400, detail="景點編號不正確")

    cursor.execute("SELECT image_url FROM images WHERE attraction_id = %s", (attraction_id,))
    images = cursor.fetchall()
    attraction['images'] = [image['image_url'] for image in images]
    print(f"lollolol, I got it:{attraction}")
    
   
  except mysql.connector.Error as e:
    print(f"Error connecting to Attractions_id: {e}")
    raise HTTPException(status_code=500, detail="伺服器內部錯誤")
  finally:
    if cursor:
        cursor.close()
    if cnx:
        cnx.close()
        
    return{"data": attraction}
    #return Attraction(**attraction)  # 返回符合 Attractions 模型的資料結構

#3rd MRT api
@app.get("/api/mrts")
def get_mrts():
    cnx = get_db_connection()
    cursor = cnx.cursor(dictionary=True)
    cursor.execute("""
        SELECT mrt, COUNT(*) as attraction_count 
        FROM attractions 
        GROUP BY mrt 
        ORDER BY attraction_count DESC
    """)
    mrt_data = cursor.fetchall()
    mrt_stations = [mrt['mrt'] for mrt in mrt_data]

    cursor.close()
    cnx.close()
    return {"data": mrt_stations}

#異常的json response:
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": True, "message": exc.detail},
    )


# localhost test
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)