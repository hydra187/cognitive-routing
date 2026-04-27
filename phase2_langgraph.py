import os
import json
from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.tools import tool
from dotenv import load_dotenv

load_dotenv()

# Initialize the LLM
# We use Groq as requested in the implementation plan (Llama-3-8b-8192 or similar)
# Requires GROQ_API_KEY in .env

@tool
def mock_searxng_search(query: str) -> str:
    """Returns hardcoded, recent news headlines based on keywords."""
    query = query.lower()
    if "crypto" in query or "bitcoin" in query:
        return "Bitcoin hits new all-time high amid regulatory ETF approvals"
    elif "ai" in query or "artificial intelligence" in query or "openai" in query:
        return "OpenAI unveils new AI model that outperforms previous generations on coding tasks"
    elif "economy" in query or "rates" in query or "fed" in query:
        return "Federal reserve signals potential rate cuts as inflation cools"
    else:
        return "Global markets show mixed reactions to recent geopolitical events"

# Define the state for LangGraph
class AgentState(TypedDict):
    bot_id: str
    persona: str
    search_query: str
    search_results: str
    final_post: str # JSON string

# Node 1: Decide Search
def decide_search(state: AgentState):
    llm = ChatGroq(model="llama-3.1-8b-instant", temperature=0.7)
    prompt = f"""You are the following bot persona:
{state['persona']}

Based on your persona, decide what topic you want to post about today.
Return ONLY a short search query that you would type into a search engine to get recent news about your topic. Do not include quotes or extra text.
"""
    response = llm.invoke([SystemMessage(content=prompt)])
    query = response.content.strip()
    return {"search_query": query}

# Node 2: Web Search
def web_search(state: AgentState):
    query = state['search_query']
    # Execute the mock tool
    result = mock_searxng_search.invoke({"query": query})
    return {"search_results": result}

# Node 3: Draft Post
def draft_post(state: AgentState):
    prompt = f"""You are the following bot persona:
{state['persona']}

Context (Recent News):
{state['search_results']}

Draft a highly opinionated, 280-character post based on the context above.
You MUST output your response as a STRICT JSON object exactly matching this format:
{{
  "bot_id": "{state['bot_id']}",
  "topic": "<the general topic of the post>",
  "post_content": "<your 280-character post>"
}}

Output ONLY the JSON object and nothing else. No markdown blocks, no introductory text.
"""
    # Enforce JSON output using response_format
    llm_json = ChatGroq(model="llama-3.1-8b-instant", temperature=0.7).bind(response_format={"type": "json_object"})
    response = llm_json.invoke([SystemMessage(content=prompt)])
    
    return {"final_post": response.content.strip()}

# Build the Graph
workflow = StateGraph(AgentState)
workflow.add_node("decide_search", decide_search)
workflow.add_node("web_search", web_search)
workflow.add_node("draft_post", draft_post)

workflow.set_entry_point("decide_search")
workflow.add_edge("decide_search", "web_search")
workflow.add_edge("web_search", "draft_post")
workflow.add_edge("draft_post", END)

app = workflow.compile()

def run_content_engine(bot_id: str, persona: str):
    initial_state = {
        "bot_id": bot_id,
        "persona": persona,
        "search_query": "",
        "search_results": "",
        "final_post": ""
    }
    result = app.invoke(initial_state)
    return result["final_post"]

if __name__ == "__main__":
    from phase1_router import BOT_PERSONAS
    # Test with Bot A
    print(run_content_engine("Bot A (Tech Maximalist)", BOT_PERSONAS["Bot A (Tech Maximalist)"]))
