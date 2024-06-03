
from langchain_community.callbacks import StreamlitCallbackHandler
from chat.ChatFactory import ChatFactory
from AgentMint import AgentMint
import streamlit as st
from dotenv import load_dotenv
import os
load_dotenv()

sidebar_logo = "https://minthcm.org/wp-content/uploads/2021/03/minthcm-logo.svg"
main_body_logo = "https://minthcm.org/wp-content/uploads/2021/03/minthcm-logo.svg"
st.logo(sidebar_logo, icon_image=main_body_logo)
st.set_page_config(page_title="Chat with MintHCM", page_icon=sidebar_logo, layout="wide")
st.title("Chat with MintHCM")


agent  = AgentMint()

# uncomment the following lines to enable tracing and set the API key
#os.environ["LANGCHAIN_TRACING_V2"] = "true"
#os.environ["LANGCHAIN_API_KEY"] = os.getenv("LANGCHAIN_API_KEY")

def new_chat():
    agent.history.clear()
    st.session_state.steps = {}

# initilate st.session_state.steps if it does not exist
if "steps" not in st.session_state:
    st.session_state.steps = {}

avatars = {"human": "user", "ai": "assistant"}
for idx, msg in enumerate(agent.history.messages):
    with st.chat_message(avatars[msg.type]):
        # Render intermediate steps if any were saved
        for step in st.session_state.steps.get(str(idx), []):
            if step[0].tool == "_Exception":
                continue
            with st.status(f"**{step[0].tool}**: {step[0].tool_input}", state="complete"):
                st.write(step[0].log)
                st.write(step[1])
        st.write(msg.content)

with st.sidebar:
    use_provider = st.selectbox(
        "Choose the provider",
        options = ChatFactory.get_providers(),
        key="use_provider"
    )
    use_model = st.selectbox(
        "Choose the model",
        options = ChatFactory.get_models(use_provider),
        key="use_model"
    )
    use_tools = st.multiselect(
        "Choose the tools",
        options = agent.get_tool_names(),
        default= agent.default_tools,
        key="use_tools"
    )
    username = st.text_input("Mint Username", key="username")
    st.sidebar.button("New Chat", on_click=new_chat, type='primary')

if user_input := st.chat_input(placeholder="How can I help you?"):
    if not username:
        st.info("Please give your Username.")
        st.stop()
    st.chat_message("user").write(user_input)

    with st.chat_message("assistant"):
        st_cb = StreamlitCallbackHandler(st.container(), expand_new_thoughts=False)

        response = agent.invoke(user_input , st_cb, use_tools, use_provider, use_model, username)

        print(response)
        st.write(response["output"])
        st.session_state.steps[str(len(agent.history.messages) - 1)] = response["intermediate_steps"]