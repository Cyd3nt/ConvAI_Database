#drop queries
DROP_TABLE_USER = ''' DROP TABLE IF EXISTS user_details CASCADE; '''

DROP_TABLE_USAGE = ''' DROP TABLE IF EXISTS usage_details ; '''

DROP_TABLE_API_PLAN_USAGE = ''' DROP TABLE IF EXISTS api_plan_usage ; '''

#queries for creating corresponding tables
CREATE_TABLE_USER = ''' CREATE  TABLE user_details (
                        user_id VARCHAR UNIQUE,
                        username VARCHAR UNIQUE,
                        email TEXT UNIQUE,
                        api_key TEXT PRIMARY KEY
                    );'''

CREATE_TABLE_USAGE = ''' CREATE TABLE usage_details (
                        usgae_id INTEGER GENERATED ALWAYS AS IDENTITY,
                        api_key TEXT NOT NULL,
                        activity_time TIMESTAMP NOT NULL,
                        service_accessed TEXT NOT NULL,
                        FOREIGN KEY(api_key) REFERENCES user_details(api_key) 
                        ON UPDATE CASCADE
                        ON DELETE CASCADE
                    );'''

CREATE_API_PLAN_USAGE = ''' CREATE TABLE api_plan_usage (
                        api_key TEXT PRIMARY KEY,
                        playground_usage_counter INTEGER DEFAULT 0 NOT NULL,
                        te_usage_counter INTEGER DEFAULT 0 NOT NULL,
                        payment_plan TEXT,
                        FOREIGN KEY(api_key) REFERENCES user_details(api_key)
                    );'''

#queries for inserting into the tables
INSERT_USER_DETAILS = '''INSERT INTO user_details(user_id, username, email, api_key) VALUES (%s, %s, %s, %s); '''

INSERT_USAGE_DETAILS = ''' '''

INSERT_API_PLAN_USAGE_DETAILS = ''' '''

#queries for viewing data
# To be done later