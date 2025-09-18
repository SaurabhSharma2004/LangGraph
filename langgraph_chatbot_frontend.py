import streamlit as st
from langchain_core.messages import HumanMessage
from langgraph_chatbot_backend import chatbot, retrieve_all_threads
import uuid

def generate_thread_id():
    return str(uuid.uuid4())

def reset_chat():
    thread_id = generate_thread_id()
    st.session_state['message_history'] = []
    if thread_id not in st.session_state['chat_threads']:
        st.session_state['chat_threads'].append(thread_id)
    st.session_state['thread_id'] = thread_id

def add_thread(thread_id):
    if thread_id not in st.session_state['chat_threads']:
        st.session_state['chat_threads'].append(thread_id)

def load_conversation(thread_id):
    st.session_state['thread_id'] = thread_id
    state = chatbot.get_state({'configurable': {'thread_id': thread_id}})
    messages = state.values.get('messages', [])
    st.session_state['message_history'] = [{'role': 'user' if isinstance(msg, HumanMessage) else 'assistant', 'content': msg.content} for msg in messages]

if 'message_history' not in st.session_state:
    st.session_state['message_history'] = []

if 'thread_id' not in st.session_state:
    st.session_state['thread_id'] = generate_thread_id()

if 'chat_threads' not in st.session_state:
    st.session_state['chat_threads'] = retrieve_all_threads()

# config = {'configurable': {'thread_id': st.session_state['thread_id']}}

config = {
    'configurable': {'thread_id': st.session_state['thread_id']},
    'metadata': {'thread_id': st.session_state['thread_id']},
    'run_name': 'chat_turn'
} # to create new thread for every new conversation in LangSmith

add_thread(st.session_state['thread_id'])

# *********************Sidebar section************************

st.sidebar.title("LangGraph Chatbot")

if st.sidebar.button("New Chat"):
    reset_chat()

st.sidebar.header("My Conversations")

for thread_id in st.session_state['chat_threads'][::-1]:
    if st.sidebar.button(thread_id):
        load_conversation(thread_id)

for message in st.session_state['message_history']:
    with st.chat_message(message['role']):
        st.text(message['content'])

user_input = st.chat_input("Type here...")

if user_input:
    st.session_state['message_history'].append({'role': 'user', 'content': user_input})
    with st.chat_message('user'):
        st.text(user_input)
    
    # response = chatbot.invoke({'messages': [HumanMessage(content=user_input)]}, config=config)

    # ai_message = response['messages'][-1].content

    # st.session_state['message_history'].append({'role': 'assistant', 'content': ai_message})

    # with st.chat_message('assistant'):
    #     st.text(ai_message)

    # Streaming the response
    with st.chat_message('assistant'):
        ai_message = st.write_stream(
             message_chunk.content for message_chunk, metadata in chatbot.stream(
                {'messages': [HumanMessage(content=user_input)]}, config=config,
                stream_mode='messages'
            )
        )
    st.session_state['message_history'].append({'role': 'assistant', 'content': ai_message})