from flask import Flask
from flask import request
import time
from db_funcs import *

app = Flask(__name__)

'''
For registering the user, the api is expecting request in the following format:
{
    "username":"thunderbird",
    "user_id":"AEXP0987",
    "api_key":"ASDFGHJK23L",
    "email":"amexdeli@f.com"
}
And return will be :
{
    "status":"success"
}
'''
@app.route("/register_user", methods=["POST"])
def registerUser():
    start = time.time()

    data = request.get_json()

    username = data["username"]
    user_id = data["user_id"]
    email = data["email"]
    api_key = data["api_key"]
    
    r=register_user(user_id, username, email, api_key)

    if r==1:
        response = {"status":"success"}
    else:
        response = {"status":"failed"}

    end = time.time()
    print("Time taken : ",end-start)

    return response

if __name__ == "__main__":
    host = '127.0.0.1'
    port = 9090
    app.run(host=host, port=port, debug=True, threaded=True, use_reloader=True,)