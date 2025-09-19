from langgraph.graph import StateGraph, START, END
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, BaseMessage
from langgraph.checkpoint.sqlite import SqliteSaver
from dotenv import load_dotenv
from typing import TypedDict, Annotated
from langgraph.graph.message import add_messages
import sqlite3
import requests
from langchain_core.tools import tool
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_community.tools import DuckDuckGoSearchRun

load_dotenv()

searchTool = DuckDuckGoSearchRun()

@tool
def calculator_tool(first_num: float, second_num: float, operation: str) -> dict:
    """A simple calculator tool that can perform basic arithmetic operations."""
    
    if operation == 'add':
        res = first_num + second_num
    elif operation == 'subtract':
        res = first_num - second_num
    elif operation == 'multiply':
        res = first_num * second_num
    elif operation == 'divide':
        if second_num == 0:
            raise ValueError("Cannot divide by zero.")
        res = first_num / second_num
    else:
        raise ValueError(f"Unsupported operation: {operation}")
    return {'result': res}

@tool
def stock_price_tool(symbol: str) -> dict:
    """fetch the latest stock price for a given ticker symbol."""
    url = f'https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey=G4ZOYS5UFQK1FIM0'
    response = requests.get(url)
    return response.json()

tools = [calculator_tool, stock_price_tool, searchTool]

llm = ChatGoogleGenerativeAI(model='gemini-2.5-flash')

llm_with_tools = llm.bind_tools(tools)

class ChatState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]

def chat_node(state: ChatState):
    messages = state['messages']
    response = llm_with_tools.invoke(messages)
    return {'messages': [response]}

tool_node = ToolNode(tools)

graph = StateGraph(ChatState)

graph.add_node('chat_node', chat_node)
graph.add_node('tools', tool_node)

graph.add_edge(START, 'chat_node')
graph.add_conditional_edges('chat_node', tools_condition)
graph.add_edge('tools', 'chat_node')

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