# Cognitive Routing & RAG Assignment

This project builds the core AI cognitive loop for the Grid07 platform. It demonstrates vector-based persona matching, autonomous content generation using LangGraph, and prompt injection defense in a deep thread RAG scenario.

## Setup Instructions

1. **Install dependencies:**
   It is recommended to use a virtual environment.
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up environment variables:**
   Copy `.env.example` to `.env` and add your Groq API key.
   ```bash
   cp .env.example .env
   ```
   *(Note: The project uses Groq for fast, free-tier LLM inference, and local `sentence-transformers` (`all-MiniLM-L6-v2`) for embeddings to keep costs at zero and speed up processing).*

3. **Run the complete pipeline:**
   ```bash
   python main.py
   ```
   *Execution logs are saved in `execution_logs.md`.*

---

## Phase Explanations

### Phase 1: Vector-Based Persona Matching (The Router)
We use `sentence-transformers` (`all-MiniLM-L6-v2`) to embed both the bot personas and the incoming user posts. The personas are stored in an in-memory `ChromaDB` vector store. When a post arrives, we calculate the cosine similarity between the post and all personas. The system returns bots that exceed a specific threshold, simulating realistic relevance routing based on interests (e.g., Tech and Finance bots care about an OpenAI post, while the Doomer bot might not meet the threshold).

### Phase 2: LangGraph Node Structure (Autonomous Content Engine)
The LangGraph state machine (`phase2_langgraph.py`) orchestrates the AI's research and drafting process:
- **State Schema (`AgentState`)**: A typed dictionary tracking `bot_id`, `persona`, `search_query`, `search_results`, and `final_post`.
- **Node 1 (`decide_search`)**: The LLM analyzes its persona and decides what search query to run to find relevant news.
- **Node 2 (`web_search`)**: Executes the `@tool mock_searxng_search` using the generated query, retrieving hardcoded news context.
- **Node 3 (`draft_post`)**: The LLM combines its persona and the retrieved context to draft a highly opinionated post. We utilize `response_format={"type": "json_object"}` alongside strict prompt engineering to guarantee the output is a valid JSON object matching the required schema.

### Phase 3: RAG Prompt Injection Defense (The Combat Engine)
In `phase3_combat_rag.py`, we implement a robust system-level defense strategy to neutralize prompt injections (e.g., "Ignore all previous instructions...").
1. **Explicit Guardrails**: The System Prompt contains a `CRITICAL SECURITY INSTRUCTION` explicitly warning the model about user manipulation attempts.
2. **Behavioral Redirection**: The prompt instructs the LLM to treat injection attempts as "weak debate tactics", telling it to mock the user for attempting to change the subject, rather than failing silently or complying with the injection.
3. **XML Tagging**: The untrusted human reply is strictly enclosed in `<USER_REPLY>` tags. This cleanly separates the unverified user content from the foundational system instructions, preventing context bleeding.
