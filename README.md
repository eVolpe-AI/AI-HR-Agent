# mint_agent_demo

## Graph structure
<img src="mint_agent/utils/graph_schema.png" alt="graph image" width="350"/>

## Installation

1. Set up envrinment with python ( Tested on: 3.12.5)

2. Prepare mongoDB database

3. Run on envrionment required installs:
    ```sh
    pip install -r requirements.txt
    ```
4. Copy .env_example as .env and fill in required fields

    required fileds for now:
    ```
    ANTHROPIC_API_KEY
    LANGCHAIN_API_KEY

    MONGO_URI
    DB_NAME

    MINT_API_URL

    LOG_LEVEL
    LOG_TO_CONSOLE
    LOG_FILE
    LOG_COLORING_IN_FILE
    ```

5. Prepare database structure:
    1. Copy credentials.json_example as credentials.json and fill in required fields.
    
        Example:
        ```json
            [
              {
                "_id": "admin",
                "auth_token": "test_token_123",
                "user_credentials": [
                  {
                    "system": "MintHCM",
                    "credential_type": "APIV8",
                    "credentials": {
                      "client_id": "test_id",
                      "secret": "test_secret"
                    }
                  }
                ]
              }
            ]
        ```
    2. Run script to populate database:
        ```sh
        python utils/generate_credentials.py
        ```

## Running the App:

1. Run the app: 
    * Test chat widget:
        ```sh
        uvicorn server:app_http --host=0.0.0.0 --port=80
        ```
    * Agent API:
        ```sh
        uvicorn server:app_ws --host=0.0.0.0 --port=5288
        ```

2. Use test chat widget on `localhost:80` or connect to websocket: `ws://localhost:5288/<user_id>/<chat_id>/<token>?advanced=<advanced>` where:
    * **`user_id`**: User ID
    * **`chat_id`**: The ID of a chat, responsible for maintaining conversation history
    * **`token`**: User authentication token
    * **`advanced`**:
        * **true** -> sends information about using all tools
        * **false** -> hides information about using safe tools
    
    * *Usage example in python*
        ```python
        import websockets
        import asyncio

        async def connect():
            uri = "ws://localhost:5288/admin/new_chat_1/test_token_123?advanced=false"
            async with websockets.connect(uri) as websocket:
                await websocket.send("Hello, World!")
                response = await websocket.recv()
                print(response)

        asyncio.run(connect())
        ```