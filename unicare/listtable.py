import mysql.connector

mydb = mysql.connector.connect(
    host ="YOUR_CLUSTER_WRITER",
    user ="UnicornAdmin",
    password ="UnicornsRock!",
    database="healthdb"
)

mycursor = mydb.cursor()

# List all tables
mycursor.execute("SHOW COLUMNS FROM health;")
myresult = mycursor.fetchall()
 
for x in myresult:
    print(x)



