# NOTE : This script resets the tables in the database

from db_utils01 import *
from queries import *

if __name__=="__main__":
    conn = connect_to_database()
    cur = conn.cursor()
    
    try:
        cur.execute(DROP_TABLE_API_PLAN_USAGE)
        print("dropped api_plan_uage")
    except Exception as e:
        print("Unable to drop api_plan_usage table.")
        print(e)

    try:
        cur.execute(DROP_TABLE_USAGE)
        print("dropped usgae_details")
    except Exception as e:
        print("Unable to drop usage_details table.")
        print(e)

    try:
        cur.execute(DROP_TABLE_USER)
        print("dropped user_details")
    except Exception as e:
        print("Unable to drop user_details table.")
        print(e)

    try:
        cur.execute(CREATE_TABLE_USER)
        print("user_details table created.")

        try:
            cur.execute(CREATE_TABLE_USAGE)
            print("usage_details table created.")
        except Exception as e:
            print(e)

        try:
            cur.execute(CREATE_API_PLAN_USAGE)
            print("api_plan_usage table created.")
        except Exception as e:
            print(e)

        
    except Exception as e:
        print(e)

    disconnect_database(conn, cur)
