# AI-HR-Agent
AI HR Agent is first free and open-source AI chatbot for [MintHCM](https://github.com/minthcm/minthcm/) created by [eVolpe.ai](https://evolpe.ai) 

You can use this chatbot to search for and change information in your MintHCM system.

Designed to simplify and streamline your workflow, our AI agent allows you to use natural language to communicate directly with your MintHCM system.

Accessible via a WebSocket API, our agent acts as an external server that utilizes MintHCM API and direct Mint database calls to get things done. And the best part? You interact with it using an intuitive chat widget inside MintHCM.

### What can it do? 
Our agent comes equipped with tools to help you perform a variety of tasks, including:
* 📅 **Checking your schedule** - It can fetch information about your upcoming meetings and calls.
* 💼 **Employee and candidate lookup** - Retrieving information about employees or candidates.
* 📝 **Creating records** - From scheduling meetings or calls to adding new candidates and more.
* 🔄 **Updating existing records** - Easily modify existing entries, like adding participants to existing meetings

### Human supervision for important actions
A human in-the-loop mechanism allows for the user to oversee bot's tool usage. This means you can approve or decline the agent's actions before they're executed - giving you control while still benefiting from the automation.

## Limitations

1. **LLM non-determinism** Like any large language model, responses can vary and are not always deterministic. This leads to the fact that the agent doesn't always choose the correct tools, as it may try different approaches to reach a solution.
2. **LLM compatibility** While our agent is designed to work with various LLMs, currently we provide interfaces only for OpenAI and Anthropic models. 
3. **Tool restrictions**: 
    * The lack of user consent for utilizing a tool at the moment makes the agent unlikely to attempt using that tool in further conversation. In such cases, it is recommended to create a new chat with a clean history.
    * Some tools are now restricted to operating only on certain modules due to the ease of testing and to narrow down options for the LLM so it provides more reliable results.
    * Instead of asking the user for missing information when using a certain tool, the agent can fabricate some details (e.g. function arguments)
4. **Time handling** - Currently, the agent can't deal with database date formats. This means that when your prompt includes dates, times, or any requests related to specific hours, the results can be inaccurate.
5. **History management** - Token-based history management works as a rough approximation and should not be considered a reliable method for systems aiming to limit token usage.

## Agent Structure
We are utilizing <a href="https://www.langchain.com/langgraph" target="_blank">LangGraph</a> to create the architecture of our agent. The following structure is a backbone of our solution:
<p align="center">
<img src="mint_agent/utils/graph_schema.png" alt="graph image" width="350"/>
</p>

1. **gear_manager_node:** Currently responsible for setting the prompt in a new conversation.
2. **history_manager_node:** Depending on the selected history management method, it creates summaries and removes redundant messages.
3. **llm_node:** Responsible for communication with the chosen LLM API.
4. **tool_controller_node:** Verifies whether the tool selected by the LLM is on the list of safe tools.
5. **tool_node:** Executes the tool selected by the LLM.

## Available configuration

### Tools
All tools are located in a `tools` directory. ToolController defines and manages the tools available to the agent. It provides three configurable lists:
* `available_tools` - all tools defined in the system
* `default_tools` - tools accessible to the agent by default
* `safe_tools` - tools that do not require user acceptance

List of tools:
1. `MintCreateMeetingTool` - Schedules a new meeting in the system.
2. `MintCreateRecordTool` - Creates a new record in the specified module.
3. `MintCreateRelTool` - Establishes a relationship in the meetings module.
4. `MintDeleteRecordTool` - Deletes a record from the specified module.
5. `MintDeleteRelTool` - Removes a relationship from the meetings module.
6. `MintGetModuleFieldsTool` - Retrieves the fields and their types for the specified module.
7. `MintGetModuleNamesTool` - Retrieves all available modules in the system.
8. `MintGetRelTool` - Checks if relationship exists in the meetings module.
9. `MintGetUsersTool` - Retrieves a list of users in the system, including details like phone number, address, email, position, and supervisor.
10. `MintSearchTool` - Retrieves a list of records from a specified module.
11. `MintUpdateFieldsTool` - Updates fields in a specified module.
12. `CalendarTool` - Retrieves today's date.
13. `AvailabilityTool` - Retrieves data about a user's planned activities (meetings and/or calls).


### Accessible modules
Agent can get a list of modules that are available in Mint via the MintGetModuleNames tool. This tool has the option to configure a white and a black list of modules. When both lists are not used, the agent will, by default, have access to all modules. 

### Prompts
Changes to system prompts, as well as the prompts used during conversation history summarization, can be made in: `mint_agent/prompts/PromptController.py`

Additionally, each tool may have its own specific fields and general description prompt within their respective files located in: `mint_agent/tools`

### History Management
At the moment, there are 4 types of message history management available for LLMs: 2 based on the number of messages and 2 based on the number of tokens used. 
* Message-based methods:
  1. `KEEP_N_MESSAGES` -> Keep only a fixed number of messages in memory (can vary to maintain history integrity, e.g. human message must be first message in the history).
  2. `SUMMARIZE_N_MESSAGES` -> Create summary after reaching certain number of messages.
* Token-based methods (currently support only Anthropic models):
  1. `KEEP_N_TOKENS` -> Keep only messages that do not exceed a fixed number of tokens in memory.
  2. `SUMMARIZE_N_TOKENS` -> Create summary after reaching certain number of tokens.

## Installation

### MintHCM

1. Set up the MintHCM instance by following the <a href="https://minthcm.org/support/minthcm-installation-guide/" target="_blank">installation guide</a>.

### Agent Server

1. Install Poetry following the <a href="https://python-poetry.org/docs/#installation" target="_blank">installation guide</a>.

2. Prepare mongoDB database server. Refer to the <a href="https://www.mongodb.com/docs/manual/installation/" target="_blank">MongoDB installation guide</a> for instructions.

3. Install all dependencies:
    ```
    poetry install
    ```

4. Copy `.env_example` as `.env` and fill in required fields


5. Setting up credentials:
    1. Copy `mint_agent/credentials.json_example` as `mint_agent/credentials.json`.

    2. Fill in the required fields:
      Open mint_agent/credentials.json in a text editor and replace the placeholder values: `<user_id>`, `<mint_user_id>`, `<client_id>`, `<client_secret>` with your actual information.
        * `_id`: The unique identifier for the user in the Agent mongoDB database.
        * `mint_user_id`: The user’s ID within the MintHCM system.
        * `client_id`: The API client ID for accessing MintHCM.
        * `secret`: The API secret key associated with the client ID.
        
        Follow this <a href="https://minthcm.org/support/how-to-use-mint-api/" target="_blank">instruction</a> on how to get `client_id` and `secret` for your user.

    2. Run script to populate database:
        ```sh
        poetry run generate_credentials
        ```

### MintHCM Agent package

1. **Prerequisites**: Ensure you have Node.js installed on your system. The supported Node.js versions range from v16 to v21. If you haven't installed Node.js yet, you can use the <a href="https://github.com/nodesource/distributions" target="_blank">NodeSource installer</a> to set it up.

2. Install <a href="https://github.com/eVolpe-AI/AI-HR-MintHCM-Package" target="_blank">mint_agent_package</a> via Module Loader

3. Navigate to the `vue` directory:
    ```
    cd /path/to/your/MintHCM/vue
    ```

4. Install node modules:
    ```
    npm install
    ```

5. Run build script:
    ```
    npm run build:repo
    ```

6. Run Quick Repair 

7. Clear cache

8. Open `api/constants/AiChat.php` and set service domain to your agent server:
    ```
    ...
    'service_domain' => 'agent.domain.example',
    ...
    ```

## Running the Agent:

1. Run the agent in preferred mode: 
    * Run Agent server (`dev` runs uvicorn with auto-reload enabled):
      ```sh
      poetry run dev # For development mode
      poetry run prod # For production mode
      ```
    * (Optional) You can evaluate the agent outside the Mint environment by running a test chat (available at `localhost:80`, may require adjusting API address in `connectWebSocket` function in `utils/chat.html`)
      ```sh
      poetry run test_chat
      ``` 
2. Start talking to Agent via chat widget available in MintHCM