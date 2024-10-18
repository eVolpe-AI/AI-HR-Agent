# mint_agent_demo

## General Description TODO:

## Sample Use Cases FIXME:
1. Getting information about user's calendar
2. Get information about users available in the system
3. Creating new records e.g. meetings, calls, candidates
4. Creating relationships between records
5. Updating records

## Limitations FIXME:

1. LLM Non-determinism: Like any large language model, responses can vary and are not always deterministic.
2. Tool Selection: The agent doesn't always choose the correct tools, as it may try different approaches to reach a solution.
3. Tool restriction: The lack of user consent for utilizing a tool at the moment makes the agent unlikely to attempt using that tool in further conversation. In such cases, it is recommended to create a new chat with clean history.
4. Missing Data: Instead of asking the user for missing information when using certain tool, the agent can fabricate some details (e.g. function arguments)
5. Time Zone Handling: Currently, time zone support is not available. This means that when your prompt includes dates, times, or any requests related to specific hours, the results can sometimes be inaccurate.
6. Token-based history management works as a rough approximation and should not be considered a reliable method for systems aiming to limit token usage.

## Mint Prerequisites
TODO

## Graph structure
<p align="center">
<img src="mint_agent/utils/graph_schema.png" alt="graph image" width="350"/>
</p>

1. **gear_manager_node:** Currently responsible for setting the prompt in a new conversation.
2. **history_manager_node:** Depending on the selected history management method, it creates summaries and removes redundant messages.
3. **llm_node:** Responsible for communication with the chosen LLM API.
4. **tool_controller_node:** Verifies whether the tool selected by the LLM is on the list of safe tools.
5. **tool_node:** Executes the tool selected by the LLM.

## Installation
1. Install Poetry: https://python-poetry.org/docs/

2. Prepare mongoDB database

3. Install all dependencies:
    ```
    poetry install
    ```

4. Copy .env_example as .env and fill in required fields

    required fields for now:
    ```
    # Anthropic API
    ANTHROPIC_API_KEY = <ANTHROPIC_API_KEY>

    # Agent Configuration
    LLM_PROVIDER = ANTHROPIC
    LLM_MODEL = claude-3-haiku-20240307

    #Agent mongo database
    MONGO_URI = <MONGO_DB_URI>
    DB_NAME = <DB_NAME>

    #MintHCM mysql database
    MINTDB_URI = <MINTDB_URI>
    MINTDB_PORT = <MINTDB_PORT>
    MINTDB_USER = <MINTDB_USER>
    MINTDB_PASS = <MINTDB_PASSWORD>
    MINTDB_DATABASE_NAME = <MINTDB_DATABASE_NAME>

    #MintHCM API
    MINT_API_URL = <MINT_API_URL>

    #Agent websocket API
    API_IP = <API_IP> -> IP address where the WebSocket API will be available
    API_PORT = <API_PORT> -> Port where the WebSocket API will be available

    #Logging configuration
    LOG_LEVEL = <DEBUG|WARNING|ERROR>
    LOG_TO_CONSOLE = <TRUE|FALSE> -> By default, logs are written to a file. Set to `TRUE` to also log to the console
    LOG_FILE = e.g. /tmp/agent.log
    LOG_COLORING = <TRUE|FALSE> -> Enable log coloring. If set to `TRUE`, some important log information will be displayed in different colors. If set to `FALSE`, logs will have a uniform color, but color tags may remain in the log output.
    ```

5. Prepare mongoDB database:
    1. Copy credentials.json_example as credentials.json and fill in required fields.
    
        Example:
        ```json
            [
              {
                "_id": "<required>",
                "mint_user_id": "<required>",
                "user_credentials": [
                  {
                    "system": "MintHCM",
                    "credential_type": "APIv8",
                    "credentials": {
                      "client_id": "<required>",
                      "secret": "<required>"
                    }
                  }
                ]
              }
            ]
        ```
    2. Run script to populate database:
        ```sh
        poetry run generate_credentials
        ```

## Configurable

### Tools FIXME:
All tools are located in <code>tools</code> directory. ToolController defines and manages the tools available to the agent. It provides three configurable lists:
* <code>available_tools</code> - all tools defined in the system
* <code>default_tools</code> - tools accessible to the agent by default
* <code>safe_tools</code> - tools that do not require user acceptance

List of tools:
1. <code>MintCreateMeetingTool</code> - Schedules a new meeting in the system.
2. <code>MintCreateRecordTool</code> - Creates a new record in the specified module.
3. <code>MintCreateRelTool</code> - Establishes a relationship between records.
4. <code>MintDeleteRecordTool</code> - Deletes a record from the specified module.
5. <code>MintDeleteRelTool</code> - Removes a relationship between records.
6. <code>MintGetModuleFieldsTool</code> - Retrieves the fields and their types for specified module.
7. <code>MintGetModuleNamesTool</code> - Retrieves all available modules in the system.
8. <code>MintGetRelTool</code> - Retrieves relationships between records.
9. <code>MintGetUsersTool</code> - Retrieves a list of users in the system, including details like phone number, address, email, position, and supervisor.
10. <code>MintSearchTool</code> - Retrieves a list of records from a specified module.
11. <code>MintUpdateFieldsTool</code> - Updates fields in a specified module.
12. <code>CalendarTool</code> - Retrieves today's date.
13. <code>AvailabilityTool</code> - Retrieves data about a user's planned activities (meetings and/or calls).


### Mint Modules available to agent FIXME:
Agent can get list of modules that are available in mint via MintGetModuleNames tool. This tool has option to configure white and black list of modules. When both lists are not used agent will by default have access to all modules. 

### Prompts FIXME:
Changes to system prompts, as well as the prompts used during conversation history summarization, can be made in:
<code>mint_agent/prompts/PromptController.py</code>

Additionally, each tool may have its own specific fields and general description prompt within their respective files located in:
<code>mint_agent/tools</code>

### History Management
At the moment, there are 4 types of message history management available for LLMs: 2 based on the number of messages and 2 based on the number of tokens used. 
* Number of messages based methods:
  1. KEEP_N_MESSAGES -> Keep only a fixed number of messages in memory (can vary to remain history integrity e.g. human message must be first message in the history).
  2. SUMMARIZE_N_MESSAGES -> Create summary after reaching certain number of messages.
* Token based methods
  1. KEEP_N_TOKENS -> Keep only messages that do not exceed a fixed number of tokens in memory.
  2. SUMMARIZE_N_TOKENS -> Create summary after reaching certain number of tokens.

## Running the App:

1. Run the app: 
    * Agent API (`dev` runs uvicorn with auto-reload enabled):
      ```sh
      poetry run dev/prod
      ```
    * Test chat widget:
      ```sh
      poetry run test_chat
      ```
2. TODO: Jak będzie zrobiona część mintowa
<!-- 2. Use test chat widget on `localhost:80` or connect to websocket: `ws://localhost:5288/<user_id>/<chat_id>/<token>?advanced=<advanced>` where:
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
        ``` -->