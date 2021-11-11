import psycopg2
import json
import os
import sys
from queries import *

def connect_to_database():
    ''' 
        Function to establish the connection to the database 
        Arguments : None
        Returns : the connection object to the database
    '''
    cred_file = "config.json"
    with open(cred_file) as f:
        cred = json.load(f)
    
    try:
        conn = psycopg2.connect(
            host=cred["host"],
            port=cred["port"],
            database=cred["database"],
            user=cred["user"],
            password=cred["password"])
    
        conn.set_session(autocommit=True)
        print("Connected to the database.")
        return conn
    
    except Exception as e:
        print("Encountered an error in connecting to the database : ", e)
        sys.exit(os.EX_OK)
        
def disconnect_database(connection_object, cursor_object=None):
    '''
        Function to terminate the connection to the database
        Arguments :
            connection_object : the connection object
            cursor_object : the cursor object
    '''
    try:
        if cursor_object is not None :
            cursor_object.close()
        connection_object.close()
        print("Connection closed")
    except Exception as e:
        print(e)
        

def execute_query(query, args,cursor_obj):
    ''' 
        Function to execute a given query using the provided connection_obj
    ''' 
    try:
        cursor_obj.execute(query,args)
        print("Query executed successfully")
        return 1
    except Exception as e:
        #print(query)
        print("Error in executing the query : ",e)
        return 0