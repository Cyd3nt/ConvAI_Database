from queries import *
from db_utils01 import *

conn = connect_to_database()

def register_user(user_id, username, email, api_key):
    cur = conn.cursor()
    r=execute_query(INSERT_USER_DETAILS, [user_id, username, email, api_key], cur)
    cur.close()
    print(r)
    return r
