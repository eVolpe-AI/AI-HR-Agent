# mint_agent_demo

## Graph structure
![ALT TEXT](./graph_schema.png)

## Getting started

* Set up envrinment with python ( Tested on: 3.12.4)

* Prepare mongoDB database server

* Run on envrionment required installs:
    ```
    pip install -r requirements.txt -U
    ```
* copy .env_example as .env and fill in required fields

    required fileds for now:
    ```
    ANTHROPIC_API_KEY
    LANGCHAIN_API_KEY

    MONGO_URI
    DB_NAME

    MINT_API_URL       
    MINT_CLIENT_ID
    MINT_CLIENT_SECRET
    ```
 

* Run app:

    ```
    fastapi dev server.py
    ```