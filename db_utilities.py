from typing import Any
import psycopg2
import os
import sys
import pandas as pd
import configparser

def connect_to_database(n: int) -> Any :
    ''' 
        Function to establish the connection to the database
        Arguments : host number => which host to connect to
        Returns : the connection object to the database
    '''
    #cred_file = os.path.join(os.getcwd(),"config.cfg")
    cred_file = "ConvAI_Database/config.cfg"
    #cred_file = "./config.cfg"
    
    db_config = configparser.ConfigParser()
    db_config.read(cred_file)
    
    #'n' specifies which host to connect to.
    #n=1 means that we want to connect to HOST01, address of which is present in the config file
    host = "HOST0" + str(n)
    
    """
    #Code snippet for reading the information from the environment variables. Will be deployed in future iteration.

    #Host scheme :
    DB_HOST01 : api.convai.com
    DB_HOST02 : te-apis.convai.com
    DB_HOST03 : <will let you know>

    #Reading from the env var
    host = os.environ['DB_HOST01']
    user = os.environ['DB_USER']
    password = os.environ['DB_PASSWORD']

    #Reading from the config file
    db_name = db_config['DATABASE']['DB_NAME']
    db_port = db_config['DATABASE']['PORT']

    """

    try:
        conn = psycopg2.connect(
            host=db_config['DATABASE'][host],
            port=db_config['DATABASE']['PORT'],
            database=db_config['DATABASE']['DB_NAME'],
            user=db_config['DATABASE']['DB_USER'],
            password=db_config['DATABASE']['DB_PASSWORD'],
        )

        conn.set_session(autocommit=True)
        print("Connected to the database.")
        return conn

    except Exception as e:
        print("Encountered an error in connecting to the database : ", e)
        sys.exit(os.EX_OK)
        
def disconnect_from_database(connection_object : psycopg2.extensions.connection, cursor_object : psycopg2.extensions.cursor = None) -> None :
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

def execute_and_return_results(query : str, conn_obj : psycopg2.extensions.connection ) -> list:
    """
    Function to execute a given query using the provided connection_obj and return the result(s) as a list of dictionary
    Arguments :
        query : the SQL query, as a string
        conn_obj : the connection object
    """
    try:
        df = pd.read_sql_query(query, con=conn_obj)
        data = df.to_dict(orient="records")
        return data
    except Exception as e:
        # print(query)
        print("Error encountered : ", e)
        return -1
