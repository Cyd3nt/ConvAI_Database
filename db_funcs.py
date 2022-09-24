#Built-ins
from multiprocessing import Process
import re
import json
from datetime import datetime

#Local imports
from .logging import log_failed_transaction
from main.global_resources.caching_resources.conv_local_cache import conv_local_cache
from ConvAI_Database.db_utilities import connect_to_database, execute_and_return_results
from main.global_resources.caching_resources.conv_redis_cache import conv_redis_cache

remove_special_character01 = lambda a : a.replace("'","''")
remove_multi_new_line_characters = lambda a : re.sub(r'(\n\s*)+\n', '\n\n', a)

#local caches
character_name_cache      = conv_local_cache(256)
character_backstory_cache = conv_local_cache(256)
character_voice_cache     = conv_local_cache(256)
character_actions_cache   = conv_local_cache(256)
user_id_cache             = conv_local_cache(256)
word_list_cache           = conv_local_cache(256)
api_key_cache             = conv_local_cache(256)

#redis cache
character_name_cache_redisclient         = conv_redis_cache(2)
character_backstory_cache_redisclient    = conv_redis_cache(3)
character_voice_cache_redisclient        = conv_redis_cache(6)
character_action_cache_redisclient       = conv_redis_cache(7)
user_id_cache_redisclient                = conv_redis_cache(4)
word_list_cache_redisclient              = conv_redis_cache(8)
api_key_cache_redisclient                = conv_redis_cache(5)
chat_history_cache_redisclient           = conv_redis_cache(9)

def register_user(user_id : str, username : str, email : str, company_name : str, company_role : str) -> int:
    '''
    Function to register the new user in the database
    Arguments:
        user_id   : the unique user_id created for the user
        username  : the username of the user
        email     : user's email
        company_name : name of user's organisation
        company_role : user's designation
    Returns :
        int(0/-1) : whether the query execution was successful or not ( 0 : successful ; -1 : error)
    '''
    INSERT_USER_DETAILS = """ INSERT INTO user_details( user_id, username, email, organisation, user_designation) VALUES ('{}','{}','{}','{}','{}');"""
    r = -1
    with connect_to_database(1) as conn :
        try:
            username = remove_special_character01(username)
            email = remove_special_character01(email)
            company_name = remove_special_character01(company_name)
            company_role = remove_special_character01(company_role)

            query = INSERT_USER_DETAILS.format(user_id,username,email, company_name, company_role)
            
            cursor_obj = conn.cursor()
            cursor_obj.execute(query)
            cursor_obj.close()
            #print("Query executed successfully")
            r = 0
        except Exception as e:
            #print(query)
            print("Error in executing the query for register_user : ",e) 
    return r

def register_api_key(user_id : str, email : str, api_key : str ) -> int:
    '''
    Function to register the api key for the user in the database
    Arguments:
        user_id   : the unique user_id created for the user
        api_key   : the user's apikey
        email     : user's email
    Returns :
        int(0/-1) : whether the query execution was successful or not ( 0 : successful ; -1 : error)
    '''
    INSERT_NEW_API = """ INSERT INTO api_map( user_id, email, api_key) VALUES ('{}','{}','{}'); """
    r = -1
    with connect_to_database(1) as conn :
        try:
            email = remove_special_character01(email)
            query = INSERT_NEW_API.format(user_id,email, api_key)
            cursor_obj = conn.cursor()
            cursor_obj.execute(query)
            cursor_obj.close()
            #print("Query executed successfully")
            r = 0

        except Exception as e:
            #print(query)
            print("Error in executing the query for register_api_key : ",e)
            
    return r

def log_user_activity(api_key : str, service_accessed : str, source : str, user_input : str ) -> int:
    '''
    Function to log users' activities in the database
    Arguments:
        api_key              : the user's apikey
        service_accessed     : which service the user accessed
        source               : from where the request originated => web gui or curl request
        user_input           : the input of the user
    Returns :
        int(0/-1)            : whether the query execution was successful or not ( 0 : successful ; -1 : error)
    '''
    INSERT_USER_ACTIVITY = """ INSERT INTO user_activity( api_key, service_accessed, source, input) VALUES ('{}','{}','{}','{}'); """
    r = -1
    with connect_to_database(1) as conn:
        try:
            user_input = remove_special_character01(user_input)
            source = remove_special_character01(source)
            service_accessed = remove_special_character01(service_accessed)
            
            query = INSERT_USER_ACTIVITY.format(api_key, service_accessed, source, user_input)
            cursor_obj = conn.cursor()
            cursor_obj.execute(query)
            cursor_obj.close()
            #print("Query executed successfully")
            r = 0
        except Exception as e:
            #print(query)
            print("Error in executing the query for log_user_activity : ",e)
            
    return r

def get_api_key_info(email : str ) -> str:
    '''
    Function to retrieve the user's api_key the database
    Arguments:
        email   : the user's email id
    Returns :
        str     : returns the latest api_key registered against the email id;
                  will return -1 in-case no api_key found in the database
    '''
    GET_API_KEY_DETAILS = """ SELECT api_key
                          FROM (SELECT api_key, generation_timestamp AS gt FROM api_map WHERE email = '{}' ORDER BY gt DESC) AS S
                          LIMIT 1; """
    GET_CONVAI_VERIFICATION_STATUS = """ SELECT convai_verified FROM user_details WHERE email ILIKE '{}'; """
    user_verification_details = {"apiKey":-1, "convai_verified" : "not verified"}
    with connect_to_database(1) as conn:
        try :
            email = remove_special_character01(email)
            api_key_query = GET_API_KEY_DETAILS.format(email)
            api_key_query_results = execute_and_return_results(api_key_query, conn)

            convai_ver_status_query = GET_CONVAI_VERIFICATION_STATUS.format(email)
            convai_ver_status_query_result = execute_and_return_results(convai_ver_status_query, conn)
        
            if len(api_key_query_results) > 0:
                user_verification_details['apiKey'] = api_key_query_results[0]['api_key']

            if len(convai_ver_status_query_result) > 0:
                user_verification_details["convai_verified"] = convai_ver_status_query_result[0]['convai_verified']

        except Exception as e:
            #print(query)
            print("Error in executing the query for get_api_key_info : ",e)
    
    return user_verification_details

def user_login(email : str ) -> dict:
    '''
    Function to retrieve the user's api_key from the database
    Arguments:
        email   : the user's email id
    Returns :
        str     : returns the latest api_key registered against the email id;k
                  will return -1 in-case no api_key found in the database
    IMPNOTE : This function performs the same functionality as the get_api_key_info(). 
              Only difference is the return type.
              Havent removed it in the current build as not sure whether which function is being used in the middleman script.
              Will remove in the future iteration.
    '''
    GET_API_KEY_DETAILS = """ SELECT api_key
                          FROM (SELECT api_key, generation_timestamp AS gt FROM api_map WHERE email ILIKE '{}' ORDER BY gt DESC) AS S
                          LIMIT 1; """
    
    user_verification_details = {
        "apiKey": -1,
        "convai_verified": False
    }
    with connect_to_database(1) as conn:
        try :
            email = remove_special_character01(email)
            api_key_query = GET_API_KEY_DETAILS.format(email)
            api_key_query_results = execute_and_return_results(api_key_query, conn)

        
            if len(api_key_query_results) > 0:
                user_verification_details['apiKey'] = api_key_query_results[0]['api_key']

        except Exception as e:
            #print(query)
            print("Error in executing the query for user_login : ",e)
    
    return user_verification_details

def check_apiKey_existence(api_key : str, transaction_id : str = 'default' ) -> int:
    '''
    Function to check if the provided api_key exists in the database
    Arguments:
        api_key   : the api_key to be checked
    Returns :
        int     : returns 0 in-case the api_key is found in the database else will return -1
    '''
    r = api_key_cache.get(api_key)  # local cache
    if r is None:
        r = int(api_key_cache_redisclient.get(api_key)) #redis cache
        if r is None:
            r = -1
            CHECK_API_KEY_EXISTENCE = """ SELECT * FROM api_map WHERE api_key = '{}';"""
            with connect_to_database(1) as conn:
                try :
                    query = CHECK_API_KEY_EXISTENCE.format(api_key)
                    query_results = execute_and_return_results(query, conn)
                    
                    if len(query_results) > 0:
                        r = 0
                        api_key_cache.add(api_key, r)
                        api_key_cache_redisclient.add(api_key, r)

                except Exception as e:
                    dbLoggingProcess = Process(
                        target = log_failed_transaction,
                        args = (
                            transaction_id,
                            "check_apiKey_existence",
                            str(datetime.now()),
                            json.dumps({
                                "api_key": api_key,
                            }),
                            str(e),
                            ""
                        )
                    )
                    dbLoggingProcess.start()
        else:
            r = int(r)
            api_key_cache.add(api_key, r) #setting value in the local cache
    return r

def get_all_personal_characters(user_id : str) -> list:
    '''
    Function to retrieve the characters owned by the user from the database
    Arguments:
        user_id   : the user_id to be checked against
    Returns :
        list     : returns list of dictionaries for all the characters owned by the user_id
                   if no results are found, will return empty list
    '''
    data = []
    RETRIEVE_PERSONAL_CHARACTERS = """ SELECT * FROM all_characters WHERE user_id='{}' ; """

    with connect_to_database(1) as conn:
        try :
            query = RETRIEVE_PERSONAL_CHARACTERS.format(user_id)
            query_results = execute_and_return_results(query, conn)
        
            if len(query_results) > 0:
                data = query_results
        except Exception as e:
            #print(query)
            print("Error in executing the query for get_all_personal_characters : ",e)
            
    return data

def get_character_details(char_id : str ) -> dict:
    '''
    Function to retrieve the characters details from the database
    Arguments:
        char_id   : the char_id of the character
    Returns :
        dict     : returns a dict consisting of the character details
                   if no results are found, will return {"status":-1}
    '''
    data = {"status":-1}
    RETRIEVE_CHARACTER_DETAILS = """ SELECT * FROM all_characters WHERE character_id='{}' ; """

    with connect_to_database(1) as conn:
        try :
            query = RETRIEVE_CHARACTER_DETAILS.format(char_id)
            query_results = execute_and_return_results(query,conn)
        
            if len(query_results) > 0:
                data = query_results[0]
        except Exception as e:
            #print(query)
            print("Error in executing the query for get_character_details : ",e)

    return data

def get_doc_store_file_link(char_id : str ) -> str:
    '''
    Function to retrieve the doc store file link for a character from the database
    Arguments:
        char_id   : the char_id of the character
    Returns :
        str       : the link to the doc store file ;
                    incase no results were found, return "-1"
    '''
    RETRIEVE_GET_DOCSTORE_FILE_LINK = """ SELECT document_store_file_link FROM character_metadata WHERE character_id='{}' AND version = 0 ;"""
    doc_store_file_link = "-1"
    with connect_to_database(1) as conn:
        try:   
            query = RETRIEVE_GET_DOCSTORE_FILE_LINK.format(char_id)
            query_results = execute_and_return_results(query,conn)

            if len(query_results) > 0:
                doc_store_file_link = query_results[0]["document_store_file_link"]
            
            #if doc_store_file_link == '-1' or len(query_results)==0:
            #        raise ValueError('Doc store file link not available!')
        except Exception as e:
            raise Exception("Error in executing the query for get_doc_store_file_link : ",e)
    return doc_store_file_link

def get_all_characters_from_collection(collection_name : str ) -> list:
    '''
    Function to retrieve the details of all the characters from a particular collection from the database
    Arguments:
        collection_name   : the name of the collection
    Returns :
        list              : list of dictionaries consisting of character details;
                            incase no results were found, return empty list
    '''
    RETRIEVE_GET_ALL_CHARACTERS_FROM_COLLECTION = """ SELECT * FROM all_characters WHERE collection_name = '{}' ; """
    data = []
    with connect_to_database(1) as conn:
        try:
            collection_name = remove_special_character01(collection_name)   
            query = RETRIEVE_GET_ALL_CHARACTERS_FROM_COLLECTION.format(collection_name)
            query_results = execute_and_return_results(query,conn)

            if len(query_results) > 0:
                data = query_results
        except Exception as e:
            #print(query)
            print("Error in executing the query for get_all_characters_from_collection : ",e)
    return data

def get_all_character_collections() -> list:
    '''
    Function to retrieve the details of all the collections from the database
    Arguments: None
    Returns :
        list              : list of dictionaries consisting of character details;
                            incase no results were found, return empty list
    '''
    RETRIEVE_COLLECTION_STATS = """ SELECT * FROM character_collections; """
    data = []
    with connect_to_database(1) as conn:
        try:   
            query = RETRIEVE_COLLECTION_STATS
            query_results = execute_and_return_results(query,conn)

            if len(query_results) > 0:
                data = query_results
        except Exception as e:
            #print(query)
            print("Error in executing the query for get_all_character_collections : ",e)
    return data

def get_username(user_id : str) -> str:
    '''
    Function to retrieve the username for a user id from the database
    Arguments:
        user_id   : user_id whose username needs to be retrieved
    Returns :
        str       : the username for the provided user_id;
                    incase no results were found, return "-1"
    '''
    username = "-1"
    RETRIEVE_USERNAME = """ SELECT username FROM user_details WHERE user_id='{}' ;"""
    with connect_to_database(1) as conn:
        try:   
            query = RETRIEVE_USERNAME.format(user_id)
            query_results = execute_and_return_results(query,conn)

            if len(query_results) > 0:
                username = query_results[0]["username"]
        except Exception as e:
            # print(query)
            # dbLoggingProcess = Process(
            #     target = log_failed_transaction,
            #     args = (
            #         transaction_id,
            #         "get_username",
            #         str(datetime.now()),
            #         json.dumps({
            #             "user_id": user_id,
            #         }),
            #         str(e),
            #         ""
            #     )
            # )
            # dbLoggingProcess.start()
            print("Error in executing the query for get_username : ",e)
    return username

def insert_new_character(
    character_name : str,
    user_id : str,
    model_type : str,
    state_names : list,
    state_links : list,
    listing : str,
    voice_type : str,
    voice_pitch : float,
    blockchain : str,
    contract_address : str,
    mint_address : str,
    owner_address : str,
    character_actions : list = [],
    character_emotions : list = [],
    collection_name : str = 'convai_default_collection'
    ) -> str:
    '''
    Function to insert a new character into the database
    Arguments:
        character_name      : the name of the character
        user_id             : the user id of the owner
        model_type          : whether 2D or 3D
        collection_name     : name of the collection, by default it will be a part of 'convai_default_collection'
        state_names         : available states for the character 
        state_links         : links to the available state
        listing             : public or private
        voice_type          : type of voice for the character
        voice_pitch         : pitch value for the character
        character_actions   : list of actions for the character
        character_emotions   : list of emotions for the character
        blockchain          : <will ask Himadri da to fill in>
        contract_address    : <will ask Himadri da to fill in>
        mint_address        : <will ask Himadri da to fill in>
        owner_address       : <will ask Himadri da to fill in>
    Returns :
        str       : the character id for the new character;
                    incase no results were found, return "-1"
    '''

    char_id = "-1"
    
    INSERT_CHARACTER_INTO_ALLCHARACTERS = """ INSERT INTO all_characters 
                                              (character_name, collection_name, user_id, model_type, state_names, state_links, listing, voice_type, voice_pitch, blockchain, contract_address, mint_address, owner_address, character_actions, character_emotions) 
                                              VALUES
                                              ('{}','{}','{}','{}','{}','{}','{}','{}','{}','{}','{}','{}','{}','{}','{}'); """
    RETRIEVE_CHARACTERID_FROM_ALLCHARACTERS = """SELECT character_id FROM all_characters 
                                                 WHERE character_name = '{}' AND user_id = '{}' AND collection_name = '{}' 
                                                 ORDER BY timestamp DESC; """
    

    with connect_to_database(1) as conn:
        try:
            state_names = [remove_special_character01(state) for state in state_names]
            character_actions = [remove_special_character01(action) for action in character_actions]
            actions_list = character_actions.copy()
            character_emotions = [remove_special_character01(emotion) for emotion in character_emotions]

            state_names = "{" + ",".join(state_names) + "}"
            state_links = "{" + ",".join(state_links) + "}"
            character_actions = "{" + ",".join(character_actions) + "}"
            character_emotions = "{" + ",".join(character_emotions) + "}"
            
            character_name = remove_special_character01(character_name)
            collection_name = remove_special_character01(collection_name)

            query01 = INSERT_CHARACTER_INTO_ALLCHARACTERS.format(character_name, collection_name, user_id, model_type, state_names, state_links, listing, voice_type, voice_pitch, blockchain, contract_address, mint_address, owner_address, character_actions, character_emotions)
            with conn.cursor() as cursor_obj:
                cursor_obj.execute(query01)
            
            query02 = RETRIEVE_CHARACTERID_FROM_ALLCHARACTERS.format(character_name, user_id, collection_name)
            query_results = execute_and_return_results(query02,conn)

            if len(query_results) > 0:
                char_id = query_results[0]["character_id"]
                
                character_name_cache.add(char_id, character_name)
                character_voice_cache.add(char_id, voice_type)
                character_actions_cache.add(char_id, actions_list)

                character_name_cache_redisclient.add(char_id, character_name)
                character_voice_cache_redisclient.add(char_id, voice_type)
                character_action_cache_redisclient.set_list(char_id, actions_list)

        except Exception as e:
            #print(query)
            print("Error in executing the query for insert_new_character : ",e)
        
    return char_id

def get_user_count() -> int:
    '''
    Function to retrieve the total number of registered user in the database
    Arguments : None
    Returns   :
        int       : total number of registered users
    '''
    usercount = -1
    RETRIEVE_USER_COUNT = """ SELECT COUNT(user_id) AS usercount FROM user_details  ;"""
    with connect_to_database(1) as conn:
        try:   
            query = RETRIEVE_USER_COUNT
            query_results = execute_and_return_results(query,conn)

            if len(query_results) > 0:
                usercount = int(query_results[0]["usercount"])
        except Exception as e:
            #print(query)
            print("Error in executing the query for get_user_count : ",e)
    return usercount

def insert_feedback(username : str, user_email : str, rating : str, feedback : str, page : str ) -> int:
    '''
    Function to insert user feedback into the database
    Arguments:
        username       : the username of the user
        user_email     : user's email
        rating         : rating provided by the user
        feedback       : comment by the user
        page           : for which page, the user is providing the feedback
    Returns :
        int(0/-1) : whether the query execution was successful or not ( 0 : successful ; -1 : error)
    '''
    INSERT_FEEDBACK= """ INSERT INTO feedback_data (username, usermail, rating, feedback, page) VALUES ('{}', '{}', '{}', '{}', '{}');"""
    r = -1
    with connect_to_database(1) as conn :
        try:
            feedback = remove_special_character01(feedback)
            user_email = remove_special_character01(user_email)

            query = INSERT_FEEDBACK.format(username, user_email, rating, feedback, page)
            cursor_obj = conn.cursor()
            cursor_obj.execute(query)
            cursor_obj.close()
            #print("Query executed successfully")
            r = 0
        except Exception as e:
            #print(query)
            print("Error in executing the query for insert_feedback : ",e)
            
    return r

def update_character_metadata(char_id : str, backstory : str, doc_store_file_link : str, characteristics : list = ["NULL"] ) -> int :
    '''
    Function to insert updated character metadata to the database
    Arguments:
        char_id               : the character id
        backstory             : updated backstory
        doc_store_file_link   : updated doc_store_file_link
        characteristics       : list of characteristics for the character
    Returns :
        int(0/-1) : whether the query execution was successful or not ( 0 : successful ; -1 : error)

    Procedure:
     CREATE OR REPLACE PROCEDURE update_backstory_version_charactermetadata(input_character_id UUID)
                language plpgsql
                AS 
                $$  
                    declare
                           version_count INTEGER;
                    begin
                        SELECT COUNT(*) FROM character_metadata 
                        INTO version_count 
                        WHERE character_id = input_character_id;
                        
                        IF version_count>0 THEN
                            UPDATE character_metadata 
                            SET  version = (SELECT MAX(version) FROM character_metadata WHERE character_id = input_character_id )+1
                            WHERE 
                            character_id = input_character_id AND version = 0;
                        END IF;
                    end
                $$
    '''
    INSERT_BACKSTORY= """  CALL update_backstory_version_charactermetadata(input_character_id => '{}'::uuid);
                           INSERT INTO character_metadata (character_id, backstory, document_store_file_link, characteristics ) VALUES ('{}','{}','{}','{}');"""
    if isinstance(characteristics, list):
        characteristics = [remove_special_character01(characteristic) for characteristic in characteristics]
        characteristics = "{" + ",".join(characteristics) + "}"

    r = -1
    with connect_to_database(1) as conn :
        try:
            backstory = remove_special_character01(backstory)

            query = INSERT_BACKSTORY.format(char_id, char_id, backstory, doc_store_file_link, characteristics)
            cursor_obj = conn.cursor()
            cursor_obj.execute(query)
            cursor_obj.close()
            #print("Query executed successfully")
            r = 0
            character_backstory_cache.update(char_id, backstory)
            character_backstory_cache_redisclient.update(char_id, backstory)

        except Exception as e:
            #print(query)
            print("Error in executing the query for update_character_backstory : ",e)
            
    return r

def update_character_details(updated_data_dict : dict ) -> int :
    '''
    Function to update the character's details in the database
    Arguments:
        updated_data_dict : dict consisting of updated data
    Returns :
       int(0/-1) : whether the query execution was successful or not ( 0 : successful ; -1 : error)
    '''
    r = -1
    UPDATE_CHARACTER_DETAILS = """ UPDATE all_characters 
                                   SET character_name = '{}', 
                                       collection_name = '{}', 
                                       user_id = '{}', 
                                       model_type = '{}', 
                                       state_names = '{}', 
                                       state_links = '{}', 
                                       listing = '{}', 
                                       voice_type = '{}', 
                                       voice_pitch = {}, 
                                       blockchain = '{}', 
                                       contract_address = '{}', 
                                       mint_address = '{}', 
                                       owner_address = '{}',
                                       character_actions = '{}',
                                       character_emotions = '{}' 
                                   WHERE character_id = '{}'; """
    
    with connect_to_database(1) as conn:
        try:
            updated_data_dict['character_name'] = remove_special_character01(updated_data_dict['character_name'])
            updated_data_dict['collection_name'] = remove_special_character01(updated_data_dict['collection_name'])
                                                    
            #print(updated_data_dict)                                     
            if isinstance(updated_data_dict["state_links"], list):
                updated_data_dict["state_links"] = "{" + ",".join(updated_data_dict["state_links"]) + "}"
            elif updated_data_dict["state_links"] is None:
                updated_data_dict["state_links"] = "{" + "}"


            if isinstance(updated_data_dict["character_actions"], list):
                action_list = updated_data_dict["character_actions"].copy() 
                updated_data_dict["character_actions"] = "{" + ",".join(updated_data_dict["character_actions"]) + "}"

            if isinstance(updated_data_dict["character_emotions"], list):
                updated_data_dict["character_emotions"] = "{" + ",".join(updated_data_dict["character_emotions"]) + "}"
               
            if isinstance(updated_data_dict["state_names"], list):
                updated_data_dict["state_names"] = [remove_special_character01(state) for state in updated_data_dict["state_names"]]
                updated_data_dict["state_names"] = "{" + ",".join(updated_data_dict["state_names"]) + "}"
            elif updated_data_dict["state_names"] is None:
                updated_data_dict["state_names"] = "{" + "}"

            query = UPDATE_CHARACTER_DETAILS.format(updated_data_dict['character_name'], updated_data_dict['collection_name'], 
                                                    updated_data_dict['user_id'],updated_data_dict['model_type'],updated_data_dict['state_names'],
                                                    updated_data_dict['state_links'], updated_data_dict['listing'], updated_data_dict['voice_type'], 
                                                    updated_data_dict['voice_pitch'], updated_data_dict['blockchain'], updated_data_dict['contract_address'], 
                                                    updated_data_dict['mint_address'], updated_data_dict['owner_address'], updated_data_dict['character_actions'],
                                                    updated_data_dict['character_emotions'], updated_data_dict['character_id'])
            cursor_obj = conn.cursor()
            cursor_obj.execute(query)
            cursor_obj.close()
            r =0

            character_name_cache.update(updated_data_dict['character_id'],updated_data_dict['character_name'])
            character_voice_cache.update(updated_data_dict['character_id'], updated_data_dict['voice_type'])
            character_actions_cache.update(updated_data_dict['character_id'],action_list)

            character_name_cache_redisclient.update(updated_data_dict['character_id'],updated_data_dict['character_name'])
            character_voice_cache_redisclient.update(updated_data_dict['character_id'], updated_data_dict['voice_type'])
            character_action_cache_redisclient.set_list(updated_data_dict['character_id'],action_list)

        except Exception as e:
            #print(query)
            print("Error in executing the query for update_character_details : ",e)
        
    return r

def add_new_word( api_key : str, word : str, pronunciation : str, status : str, transaction_id : str, username : str = "default_name" ) -> int:
    '''
    Function to add new words for boosting to the database
    Arguments:
        username               : username
        api_key                : api key of the username
        word                   : word for boosting
        pronunciation          : pronunciation for the word
        status                 : current boosting status
    Returns :
        int(0/-1) : whether the query execution was successful or not ( 0 : successful ; -1 : error)
    '''
    INSERT_WORD_FINETUNING = """ INSERT INTO word_finetuning( username, api_key, word, pronunciation, status ) VALUES ('{}', '{}', '{}', '{}', '{}');"""
    r = -1

    with connect_to_database(2) as conn :
        try:
            word = remove_special_character01(word)
            pronunciation = remove_special_character01(pronunciation)
            status = remove_special_character01(status)

            query = INSERT_WORD_FINETUNING.format(username, api_key, word, pronunciation, status)
            cursor_obj = conn.cursor()
            cursor_obj.execute(query)
            cursor_obj.close()
            r = 0

            word_list = word_list_cache.get(api_key)
            if word_list is None:
                _ = fetch_word_list(api_key)
            else:
                word_list.append(word)
                word_list_cache.update(api_key, word_list)
                word_list_cache_redisclient.set_list(api_key, word_list)
            
        except Exception as e:
            #print(query)
            dbLoggingProcess = Process(
                target = log_failed_transaction,
                args = (
                    transaction_id,
                    "add_new_word",
                    str(datetime.now()),
                    json.dumps({
                        "api_key": api_key,
                        "word": word,
                        "pronunciation": pronunciation,
                        "status": status,
                    }),
                    str(e),
                    ""
                )
            )
            dbLoggingProcess.start()
    
    return r

def update_status_wordtuning(status : str, api_key : str, word : str ) -> int:
    '''
    Function to update the boosting status for a word
    Arguments:
        api_key                : api key of the username
        word                   : word for boosting
        status                 : current boosting status
    Returns :
        int(0/-1) : whether the query execution was successful or not ( 0 : successful ; -1 : error)
    '''
    UPDATE_STATUS_WORD_FINETUNING = """ UPDATE word_finetuning SET status = '{}' WHERE api_key = '{}' AND word = '{}';"""
    r = -1
    with connect_to_database(2) as conn :
        try:
            status = remove_special_character01(status)
            word = remove_special_character01(word)

            query = UPDATE_STATUS_WORD_FINETUNING.format(status, api_key, word)
            cursor_obj = conn.cursor()
            cursor_obj.execute(query)
            cursor_obj.close()
            r = 0
        except Exception as e:
            print("Error in executing the query for update_status_wordtuning : ",e)
    
    return r

def fetch_word_list(api_key : str, transaction_id : str = 'default' ) -> list:
    '''
    Function to retrieve the list of all the boosted words for an api_key
    Arguments:
        api_key                : api key of the username
    Returns :
        list : list of boosted words, if none found, would return empty list
    '''
    r = word_list_cache.get(api_key)
    if r is None:
        r = word_list_cache_redisclient.get_list(api_key)
        if r is None:
            GET_WORD_LIST_FOR_API_KEY = """SELECT word FROM word_finetuning WHERE api_key = '{}' ;"""
            r = [-1]
            with connect_to_database(2) as conn :
                try:
                    query = GET_WORD_LIST_FOR_API_KEY.format(api_key)
                    query_results = execute_and_return_results(query,conn)
                    if len(query_results)>0:
                        r = []
                        for i in query_results:
                            r.append(i["word"])
                        word_list_cache.add(api_key, r)
                        word_list_cache_redisclient.set_list(api_key, r)
                    elif len(query_results) == 0:
                        r = []
                        word_list_cache.add(api_key, r)
                        word_list_cache_redisclient.set_list(api_key, r)

                except Exception as e:
                    dbLoggingProcess = Process(
                        target = log_failed_transaction,
                        args = (
                            transaction_id,
                            "fetch_word_list",
                            str(datetime.now()),
                            json.dumps({
                                "api_key": api_key,
                            }),
                            str(e),
                            ""
                        )
                    )
                    dbLoggingProcess.start()
        else:
            word_list_cache.add(api_key, r)
            
    return r

def get_character_name(char_id : str) -> str:
    '''
    Function to retrieve the character name for a provided char id
    Arguments:
        char_id                : character id
    Returns :
        str                    : character name, will return -1 if not found
    '''
    r = character_name_cache.get(char_id)
    if r is None:
        r = character_name_cache_redisclient.get(char_id)
        if r is None:
            r = "-1"
            GET_CHARACTER_NAME = """ SELECT  character_name FROM all_characters WHERE character_id = '{}' ;"""
            with connect_to_database(1) as conn :
                try:
                    query = GET_CHARACTER_NAME.format(char_id)
                    query_results = execute_and_return_results(query,conn)
                    if len(query_results)>0:
                        r = query_results[0]["character_name"]
                        character_name_cache.add(char_id, r)
                        character_name_cache_redisclient.add(char_id, r)
                except Exception as e:
                    print("Error in executing the query for get_character_name : ",e)
        else:
            character_name_cache.add(char_id, r)
    return r

def get_user_ID(api_key : str) -> str:
    '''
    Function to retrieve the user id for a provided api key
    Arguments:
        api_key                : api key from the user
    Returns :
        str                    : user id, will return -1 if not found
    '''
    r = user_id_cache.get(api_key)
    if r is None:
        r = user_id_cache_redisclient.get(api_key)
        if r is None:
            r = "-1"
            RETRIEVE_USERID = """ SELECT user_id FROM api_map WHERE api_key = '{}'; """
            with connect_to_database(1) as conn :
                try:
                    query = RETRIEVE_USERID.format(api_key)
                    query_results = execute_and_return_results(query,conn)
                    if len(query_results)>0:
                        r = query_results[0]["user_id"]
                        user_id_cache.add(api_key,r)
                        user_id_cache_redisclient.add(api_key,r)
                except Exception as e:
                    print("Error in executing the query for get_user_ID : ",e)
        else:
            user_id_cache.add(api_key,r)
    return r

def write_to_chat_history(char_id : str, user_id : str, user_query: str, bot_text: str, session_id : str) -> int:
    '''
    Function to log chat history
    Arguments:
        char_id         : character's id
        user_id         : user's id
        user_query      : user's query
        bot_text        : bot's response
        session_id      : chat's session id
    Returns :
        int(0/-1) : whether the query execution was successful or not ( 0 : successful ; -1 : error)
    '''
    INSERT_CHARACTER_CHAT = """ INSERT INTO all_interactions 
                                 (user_id, character_id, session_id, user_query, response) 
                                 VALUES 
                                 ('{}', '{}', '{}', '{}', '{}'); """
    r = -1

    with connect_to_database(1) as conn :
        try:
            user_query = remove_special_character01(user_query)
            bot_text = remove_special_character01(bot_text)

            query = INSERT_CHARACTER_CHAT.format(user_id, char_id, session_id, user_query, bot_text)
            cursor_obj = conn.cursor()
            cursor_obj.execute(query)
            cursor_obj.close()
            r = 0
            #updating the cache
            update_chat_history_to_cache(char_id, user_id, session_id)
        except Exception as e:
            #print(query)
            print("Error in executing the query for write_to_chat_history : ",e)

    return r

def get_chat_history(char_id : str, user_id : str, session_id : str = "-1",from_time : str = "-1", to_time : str = "-1" ) -> list:
    '''
    Function to retrieve chat history
    Arguments:
        char_id         : character's id
        user_id         : user's id
        from_time       : start time
        to_time         : end time
        session_id      : chat's session id
    Returns :
        list : list of dictionaries, consisiting details for the chat logs. Will return empty list if none found.
    '''
    r = chat_history_cache_redisclient.get_list(session_id)
    if r is None or int(r)==-1:
        r = []

        GET_CHAT_HISTORY    = """ SELECT * FROM all_interactions WHERE user_id='{}' AND character_id='{}'  """
        GET_CHAT_HISTORY_02 = """ AND (timestamp BETWEEN '{}' AND '{}')"""
        GET_CHAT_HISTORY_03 = """ AND session_id='{}' """
        
        with connect_to_database(1) as conn :
            try:
                query = GET_CHAT_HISTORY.format(user_id, char_id)
        
                if to_time!=-1 and to_time!="-1":
                    query = query + GET_CHAT_HISTORY_02.format(to_time,from_time) 
        
                if session_id!=-1 and session_id!="-1":
                    query = query + GET_CHAT_HISTORY_03.format(session_id)

                query = query + ";"
                query_results = execute_and_return_results(query,conn)
                #print("Query executed successfully")
                if len(query_results)>0:
                    r = query_results
            except Exception as e:
                #print(query)
                print("Error in executing the query for get_chat_history : ",e)
    return r

def update_chat_history_to_cache(char_id : str, user_id : str, session_id : str = "-1",from_time : str = "-1", to_time : str = "-1" ):
    '''
    Function to retrieve chat history and store it in the redis cache
    Arguments:
        char_id         : character's id
        user_id         : user's id
        from_time       : start time
        to_time         : end time
        session_id      : chat's session id
    '''
    r = [-1]

    GET_CHAT_HISTORY    = """ SELECT * FROM all_interactions WHERE user_id='{}' AND character_id='{}'  """
    GET_CHAT_HISTORY_02 = """ AND (timestamp BETWEEN '{}' AND '{}')"""
    GET_CHAT_HISTORY_03 = """ AND session_id='{}' """
    
    with connect_to_database(1) as conn :
        try:
            query = GET_CHAT_HISTORY.format(user_id, char_id)
      
            if to_time!=-1 and to_time!="-1":
                query = query + GET_CHAT_HISTORY_02.format(to_time,from_time) 
    
            if session_id!=-1 and session_id!="-1":
                query = query + GET_CHAT_HISTORY_03.format(session_id)

            query = query + ";"
            query_results = execute_and_return_results(query,conn)
            if len(query_results)>0:
                r = query_results
                chat_history_cache_redisclient.set_list(session_id, r)
        except Exception as e:
            print("Error in executing the query for update_chat_history : ",e)
    return r

def get_backstory(char_id : str) -> str:
    '''
    Function to retrieve character's backstory
    Arguments:
        char_id         : character's id
    Returns :
        str : will return the character's backstory as a string , if not found will return -1
    '''
    r = character_backstory_cache.get(char_id)
    if r is None:
        r = character_backstory_cache_redisclient.get(char_id)
        if r is None:
            r = "-1"
            GET_CHARACTER_BACKSTORY = """ SELECT backstory FROM character_metadata WHERE character_id = '{}' AND version=0;"""
            with connect_to_database(1) as conn :
                try:
                    query = GET_CHARACTER_BACKSTORY.format(char_id)
                    query_results = execute_and_return_results(query,conn)
                    if len(query_results)>0:
                        r = query_results[0]["backstory"]
                        character_backstory_cache.add(char_id,r)
                        character_backstory_cache_redisclient.add(char_id,r)
                except Exception as e:
                    print("Error in executing the query for get_backstory : ",e)
        else:
            character_backstory_cache.add(char_id,r)
    return r

def delete_new_user(email : str)->str:
    '''
    Function to delete a new user from user_details, for the purpose of a rollback in case of failure in api key regstration.
    Arguments:
        email : the email id of the user whose record is to be deleted.
    Returns:
        str : "SUCCESS" / "ERROR: <>"
    '''
    DELETE_USER = """ DELETE FROM user_details WHERE email = '{}';"""
    with connect_to_database(1) as conn :
        try:
            email = remove_special_character01(email)
            query = DELETE_USER.format(email)
            cursor_obj = conn.cursor()
            cursor_obj.execute(query)
            cursor_obj.close()
            r = "SUCCESS"
        except Exception as e:
            #print(query)
            print("Error in executing the query for delete_new_user : ",e)
            r = """ ERROR: {} """.format(e)
    return r

def user_registration(uid, username, email, api_key, company_name, company_role ) -> dict:
    '''
    Function to streamline the user's registration process
    Arguments:
        uid         : user id
        username    : username
        email       : user's mail
        api_key     : user's api key
    Returns :
        dict : will return the registration status. 
               Keyword is "status" , if 0 then it means successful, else failure. 
               The negative int will denote at whch level it failed.
    '''
    user_registration = register_user(uid, username, email, company_name, company_role)
    if user_registration == 0:
        api_registration = register_api_key(uid, email, api_key)
        if api_registration == 0:
            return {"status":"SUCCESS"}
        else:
            #async process
            deleteUserProcess = Process(
                target=delete_new_user, args=(email)
            )
            deleteUserProcess.start()
            return {"status":"ERROR in api registration for the user."}
    else:
        return {"status":"ERROR in creating new user."}

def delete_char_ID(char_id : str ) -> str :
    '''
    Function to delete the character from all_characters
    Arguments:
        char_id : the character_id of the character to be deleted.
    Returns :
        str : will return the transaction status
            "SUCCESS" : the character is deleted
            "ERROR : <error message>" : error encountered during the operation 
    '''
    DELETE_CHARACTER = """ DELETE FROM all_characters WHERE character_id = '{}';"""
    with connect_to_database(1) as conn :
        try:
            query = DELETE_CHARACTER.format(char_id)
            cursor_obj = conn.cursor()
            cursor_obj.execute(query)
            cursor_obj.close()
            r = "SUCCESS"
        except Exception as e:
            #print(query)
            print("Error in executing the query for delete_character : ",e)
            r = """ ERROR: {} """.format(e)
    return r

def get_username_from_apiKey(apiKey : str)-> str :
    '''
    Function to retrieve the username from the provided api key
    Arguments:
        apiKey : the api key of the user
    Returns :
        str : will return the corresponding username else -1
    '''
    GET_USERNAME = """ SELECT username FROM user_details WHERE user_id = (SELECT user_id FROM api_map WHERE api_key = '{}'); """
    r = "-1"
    with connect_to_database(1) as conn :
        try:
            query = GET_USERNAME.format(apiKey)
            query_results = execute_and_return_results(query,conn)
            if len(query_results)>0:
                r = query_results[0]["username"]
        except Exception as e:
            #print(query)
            print("Error in executing the query for get_username_from_apiKey : ",e)
    return r

def get_voice_for_character(charID : str)-> str :
    '''
    Function to retrieve the voice for the provided charID
    Arguments:
        charID : the character id
    Returns :
        str : the voice of the character
        by default will return -1 (in case of any exception)
    '''
    r = character_voice_cache.get(charID)
    if r is None:
        r  = character_voice_cache_redisclient.get(charID)
        if r is None:
            GET_CHARACTER_VOICE = """ SELECT voice_type FROM all_characters WHERE character_id = '{}';"""
            r = "-1"
            with connect_to_database(1) as conn :
                try:
                    query = GET_CHARACTER_VOICE.format(charID)
                    query_results = execute_and_return_results(query,conn)
                    if len(query_results)>0:
                        r = query_results[0]["voice_type"]
                        character_voice_cache.add(charID, r)
                        character_voice_cache_redisclient.add(charID, r)
                except Exception as e:
                    print("Error in executing the query for get_voice_for_character : ",e)
        else:
            character_voice_cache.add(charID, r)
    return r

def get_character_actions(charID : str) -> list :
    '''
    Function to retrieve the available actions for a specific character
    Arguments:
        charID : the character id
    Returns:
        list : list of actions available for the character. If none are present, will return empty list.
    '''
    r = character_actions_cache.get(charID)
    if r is None:
        r = character_action_cache_redisclient.get_list(charID)
        if r is None:
            GET_CHARACTER_ACTIONS = """ SELECT character_actions FROM all_characters WHERE character_id = '{}';"""
            r = []
            with connect_to_database(1) as conn :
                try:
                    query = GET_CHARACTER_ACTIONS.format(charID)
                    query_results = execute_and_return_results(query,conn)
                    if len(query_results)>0:
                        r = query_results[0]["character_actions"]
                        character_actions_cache.add(charID,r)
                        character_action_cache_redisclient.set_list(charID,r)
                except Exception as e:
                    print("Error in executing the query for get_character_actions : ",e)
        else:
            character_actions_cache.add(charID,r)
    return r

def insert_interaction_prompt_data( prompt : str, temperature : float, max_tokens : int, top_p : float, frequency_penalty : float, presence_penalty : float, stop : str, response : str , model : str = 'NULL', engine : str = 'NULL' ) -> int :
    '''
    Function to insert openai request and responses for fututre use
    Arguments:
        prompt                   : TEXT
        model                    : TEXT
        engine                   : TEXT
        temperature              : FLOAT
        max_tokens               : INT
        top_p                    : FLOAT
        frequency_penalty        : FLOAT
        presence_penalty         : FLOAT
        stop                     : TEXT
        response                 : TEXT
    Returns:
        int : -1 if failed else 0
    '''
    INSERT_RECORD = """ INSERT into interaction_prompt_data (prompt, model, engine, temperature, max_tokens, top_p, frequency_penalty, presence_penalty, stop, response) VALUES ('{}','{}','{}', {}, {}, {}, {}, {}, '{}', '{}'); """
    r = -1
    with connect_to_database(1) as conn :
        try:
            prompt = remove_special_character01(prompt)
            prompt = remove_multi_new_line_characters(prompt)
            
            model = remove_special_character01(model)
            engine = remove_special_character01(engine)
            stop = remove_special_character01(stop)
            
            response = remove_special_character01(response)
            response = remove_multi_new_line_characters(response)
            
            query = INSERT_RECORD.format(prompt, model, engine, temperature, max_tokens, top_p, frequency_penalty, presence_penalty, stop, response)
            cursor_obj = conn.cursor()
            cursor_obj.execute(query)
            cursor_obj.close()
            r = 0
        except Exception as e:
            #print(query)
            print("Error in executing the query for insert_interaction_prompt_data : ",e)
    return r

def get_user_details(email : str)->dict:
    '''
    Function to retrieve user details.
    Return sample :
    {'user_id': 'CAIJUST-TESTING2022AR', 
    'username': 'testing', 
    'email': 'just-testing@convai.com', 
    'registration_timestamp': Timestamp('2022-04-16 06:35:23.457031'), 
    'organisation': None, 
    'user_designation': None}
    '''
    r=-1
    GET_USER_DETAILS = """SELECT * FROM user_details WHERE email = '{}'; """
    with connect_to_database(1) as conn :
        try:
            query = GET_USER_DETAILS.format(email)
            query_results = execute_and_return_results(query,conn)
            if len(query_results)>0:
                r = query_results[0]
        except Exception as e:
            #print(query)
            print("Error in executing the query for get_chat_history : ",e)
    return r

def user_update(email : str, username : str, company_name : str, company_role: str):
    '''
    Function to update user details in the table user_details.
    Returns :
    {'status': 'SUCCESS'}
    '''
    s = -1
    UPDATE_USER_DETAILS = """ UPDATE user_details SET username='{}' , organisation='{}', user_designation='{}' WHERE email='{}' ; """
    with connect_to_database(1) as conn :
        try:
            username = remove_special_character01(username)
            company_name = remove_special_character01(company_name)
            company_role = remove_special_character01(company_role)

            query = UPDATE_USER_DETAILS.format(username, company_name, company_role, email)

            cursor_obj = conn.cursor()
            cursor_obj.execute(query)
            cursor_obj.close()

            s="SUCCESS"
        except Exception as e:
            #print(query)
            print("Error in executing the query for get_chat_history : ",e)
            s="ERROR : "+str(e)

    return {"status":s}

def get_character_emotions(charID : str ) -> list:
    '''
    Function to retrieve the available emotions for a specific character
    Arguments:
        charID : the character id
    Returns:
        list : list of emotions available for the character. If none are present, will return empty list.
    '''
    GET_CHARACTER_EMOTIONS = """ SELECT character_emotions FROM all_characters WHERE character_id = '{}';"""
    r = []
    with connect_to_database(1) as conn :
        try:
            query = GET_CHARACTER_EMOTIONS.format(charID)
            query_results = execute_and_return_results(query,conn)
            if len(query_results)>0:
                r = query_results[0]["character_emotions"]
        except Exception as e:
            #print(query)
            print("Error in executing the query for get_character_emotions : ",e)
    return r

def update_api_key(email:str, api_key:str)->dict:
    '''
    Function to register the new api_key for the user at the backend.

    Procedure ;
    CREATE OR REPLACE PROCEDURE update_api_key_version_api_map(input_email TEXT, new_api_key TEXT)
                language plpgsql
                AS 
                $$  
                    declare
                           version_count INTEGER;
                           r_user_id TEXT;
                    begin
                 
                        SELECT user_id FROM api_map 
                        INTO r_user_id
                        WHERE email = input_email;
                 
				 		SELECT COUNT(*) FROM api_map 
                        INTO version_count 
                        WHERE user_id = r_user_id;
                        
						IF version_count>1 THEN
                            UPDATE api_map 
                            SET  email = version_count::TEXT 
                            WHERE 
                            email = input_email;
                        END IF;

                        INSERT INTO api_map( user_id, email, api_key) VALUES (r_user_id, input_email, new_api_key); 
                    end
                $$
    '''
    r = -1
    UPDATE_API_KEY= """  CALL update_api_key_version_api_map(input_email => '{}'::TEXT, new_api_key => '{}'::TEXT); """
    error = ""
    with connect_to_database(1) as conn :
        try:
            query = UPDATE_API_KEY.format(email, api_key)
            cursor_obj = conn.cursor()
            cursor_obj.execute(query)
            cursor_obj.close()
            r = 0
        except Exception as e:
            #print(query)
            print("Error in executing the query for update_api_key : ",e)
            error = e
    return {
            "api_key": api_key,
            "email": email,
            "status": "SUCCESS" if r==0 else "FAILED with "+str(error)
           }


def update_convai_verification_status(email:str, verification_state: str ) -> dict:
    '''
    Funtion to update the convai_verified status of the user after successful verification.
    Returns: 
    {
        'status': 'SUCCESS'
    }
    '''

    s = ""
    UPDATE_CONVAI_VER_STATUS = """ UPDATE user_details SET convai_verified='{}' WHERE email ILIKE '{}' ; """
    with connect_to_database(1) as conn:
        try:
            query = UPDATE_CONVAI_VER_STATUS.format(verification_state, email)

            cursor_obj = conn.cursor()
            cursor_obj.execute(query)
            cursor_obj.close()

            s = "SUCCESS"

        except Exception as e:
            #print(query)
            print("Error in executing the query to update convai_verified attribute for the following user ",e)
            s="ERROR : "+str(e)

    return {"status":s}

def get_conversations_from_db(sessionID : str, conversationContextLevel: int)->list:
    '''
    Function to retrieve a fix set of conversations from the database. The number of conversations to be retrieved from the database is specified by the conversationContextLevel parameter.
    '''
    r = []
    GET_INTERACTIONS= """  SELECT * FROM all_interactions WHERE session_id = '{}' ORDER BY timestamp ASC LIMIT '{}' ; """
    with connect_to_database(1) as conn :
        try:
            query = GET_INTERACTIONS.format(sessionID, conversationContextLevel)
            query_results = execute_and_return_results(query,conn)
            r = query_results
        except Exception as e:
            #print(query)
            print("Error in executing the query for get_conversations_from_db : ",e)
    return r 

def get_character_id_from_name(char_name : str) -> str:
    '''
    Function to retrieve the character id for a provided char name
    Arguments:
        char_id                : character id
    Returns :
        str                    : character name, will return -1 if not found
    '''
    r = "-1"
    GET_CHARACTER_NAME = """ SELECT  character_id FROM all_characters WHERE character_name = '{}' ;"""
    with connect_to_database(1) as conn :
        try:
            query = GET_CHARACTER_NAME.format(char_name)
            query_results = execute_and_return_results(query,conn)
            #print("Query executed successfully")
            if len(query_results)>0:
                r = query_results[0]["character_id"]
        except Exception as e:
            #print(query)
            print("Error in executing the query for get_character_name : ",e)
    
    return r

def delete_char_for_user(char_id : str, user_id: str) -> str :
    '''
    Function to delete the character from all_characters
    Arguments:
        char_id : the character_id of the character to be deleted.
    Returns :
        str : will return the transaction status
            "SUCCESS" : the character is deleted
            "ERROR : <error message>" : error encountered during the operation 
    '''
    DELETE_CHARACTER = """ DELETE FROM all_characters WHERE character_id = '{}' and user_id = '{}';"""
    with connect_to_database(1) as conn :
        try:
            query = DELETE_CHARACTER.format(char_id, user_id)
            cursor_obj = conn.cursor()
            cursor_obj.execute(query)
            cursor_obj.close()
            r = "SUCCESS"
        except Exception as e:
            #print(query)
            print("Error in executing the query for delete_character : ",e)
            r = """ ERROR: {} """.format(e)
    return r