from fastapi import *
from fastapi.responses import FileResponse
app=FastAPI()

from fastapi import FastAPI, Query, HTTPException
from pydantic import BaseModel
from typing import Optional
import mysql.connector
from mysql.connector import Error


mysql_config = {
    'host': 'localhost',
    'user': 'wehelp',
    'password': 'wehelp',
    'database': 'TaipeiDayTrip_db'
}


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

#API: Attractions
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
    images: list[str]

class ResponseModel(BaseModel):
    nextPage: Optional[int] = None
    data: list[Attraction]

def get_db_connection():
    try:
        return mysql.connector.connect(**mysql_config)
      
    except Error as e:
        print(f"Error connecting to MySQL Platform: {e}")
        raise HTTPException(status_code=500, detail="伺服器內部錯誤")

@app.get("/api/attractions", response_model=ResponseModel)
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
        
        return {"nextPage": nextPage, "data": attractions} 
    
    except mysql.connector.Error as e:
        raise HTTPException(status_code=500, detail="Database error")
    finally:
        cursor.close()
        cnx.close()
    #有時候位子對，但是顯示錯誤，主要是因為 tab 跟空格







# localhost test
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)