from langgraph.graph import StateGraph, START, END
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, BaseMessage
from langgraph.checkpoint.sqlite import SqliteSaver
from dotenv import load_dotenv
from typing import TypedDict, Annotated
from langgraph.graph.message import add_messages
import sqlite3

load_dotenv()

llm = ChatGoogleGenerativeAI(model='gemini-2.5-flash')

class ChatState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]

def chat_node(state: ChatState):
    messages = state['messages']
    response = llm.invoke(messages)
    return {'messages': [response]}

graph = StateGraph(ChatState)

graph.add_node('chat_node', chat_node)
graph.add_edge(START, 'chat_node')
graph.add_edge('chat_node', END)

connection = sqlite3.connect('chatbot.db', check_same_thread=False)

checkpointer = SqliteSaver(conn=connection, )

chatbot = graph.compile(checkpointer=checkpointer)

def retrieve_all_threads():
    all_threads = set()
    for checkpoint in checkpointer.list(None):
        config = checkpoint.config
        if 'thread_id' in config.get('configurable', {}):
            all_threads.add(config['configurable']['thread_id'])
    return list(all_threads)

# config = {'configurable': {'thread_id': 'default_thread'}}

# res = chatbot.invoke({'messages': [HumanMessage(content="what is capital of India and acknowledge my name also")]}, config=config)

# print(res)