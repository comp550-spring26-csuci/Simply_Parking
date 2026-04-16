import mysql.connector 
# 1. Establish the connection 
try: 
        db_connection = mysql.connector.connect(
        host="137.184.46.194",
        user="crsmcike_simplydb",
        password="Comp550SWE!", 
        database="crsmcikesimply_park" 
        )
 
        cursor = db_connection.cursor() 

# 2. Create a Table 
        cursor.execute("""
                CREATE TABLE IF NOT EXISTS users 
                (id INT AUTO_INCREMENT PRIMARY KEY,
                 #name VARCHAR(255),
                 email VARCHAR(255)
         )
        """) 
# 3. Insert Data 
        sql = "INSERT INTO users (name, email) VALUES (%s, %s)" 
        val = ("John Doe", "john@example.com") 
        cursor.execute(sql, val)
         # Required to save changes for INSERT/UPDATE/DELETE 

        db_connection.commit() 
        print(f"Inserted ID: {cursor.lastrowid}")


# 4. Query Data 
        cursor.execute("SELECT * FROM users") 
        for row in cursor.fetchall(): 
                print(row) 

except mysql.connector.Error as err: 
                print(f"Error: {err}") 

finally: 
        # 5. Close resources 
        if 'db_connection' in locals() and db_connection.is_connected(): 
                cursor.close() 
                db_connection.close()
#test query

