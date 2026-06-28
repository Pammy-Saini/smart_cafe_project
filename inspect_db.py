import pymysql

try:
    conn = pymysql.connect(
        host='localhost',
        user='root',
        password='pammysaini',
        db='smart_cafe_db'
    )
    cursor = conn.cursor()
    cursor.execute("DESCRIBE cafe_menu")
    print("Columns:", cursor.fetchall())
    cursor.execute("SELECT * FROM cafe_menu")
    print("Rows:", cursor.fetchall())
    cursor.close()
    conn.close()
except Exception as e:
    print("Error:", e)
