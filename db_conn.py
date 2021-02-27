import os
import mysql.connector

db_uid = os.getenv('CASKEY5_USERNAME')
db_pwd = os.getenv('CASKEY5_PASSWORD')
db_host = os.getenv('CASKEY5_HOST')

cnx = mysql.connector.connect(user=db_uid, password=db_pwd, host=db_host, database='caskey5_buffaloCrime')

print(cnx)

cnx.close()
