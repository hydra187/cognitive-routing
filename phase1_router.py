import chromadb
from sentence_transformers import SentenceTransformer
import numpy as np

# Load local embedding model (free, runs locally)
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

# Initialize in-memory ChromaDB
client = chromadb.Client()

# Create a collection for our bots
try:
    client.delete_collection("bots")
except Exception:
    pass
collection = client.create_collection("bots")

# Define the bot personas
BOT_PERSONAS = {
    "Bot A (Tech Maximalist)": "I believe AI and crypto will solve all human problems. I am highly optimistic about technology, Elon Musk, and space exploration. I dismiss regulatory concerns.",
    "Bot B (Doomer / Skeptic)": "I believe late-stage capitalism and tech monopolies are destroying society. I am highly critical of AI, social media, and billionaires. I value privacy and nature.",
    "Bot C (Finance Bro)": "I strictly care about markets, interest rates, trading algorithms, and making money. I speak in finance jargon and view everything through the lens of ROI."
}

def setup_vector_store():
    """Embed the personas and store them in ChromaDB."""
    for bot_id, persona in BOT_PERSONAS.items():
        embedding = embedding_model.encode(persona).tolist()
        collection.add(
            ids=[bot_id],
            embeddings=[embedding],
            documents=[persona],
            metadatas=[{"bot_id": bot_id}]
        )

setup_vector_store()

def cosine_similarity(v1, v2):
    """Calculate cosine similarity between two vectors."""
    v1 = np.array(v1)
    v2 = np.array(v2)
    return np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))

def route_post_to_bots(post_content: str, threshold: float = 0.3) -> list:
    """
    Given a post, find bots that care about the topic using vector similarity.
    Note: threshold is adjusted because MiniLM embeddings can have different baseline similarities.
    """
    post_embedding = embedding_model.encode(post_content).tolist()
    
    matching_bots = []
    for bot_id, persona in BOT_PERSONAS.items():
        bot_emb = embedding_model.encode(persona).tolist()
        sim = cosine_similarity(post_embedding, bot_emb)
        if sim > threshold:
            matching_bots.append((bot_id, sim))
            
    # Sort by similarity descending
    matching_bots.sort(key=lambda x: x[1], reverse=True)
    return matching_bots

if __name__ == "__main__":
    post = "OpenAI just released a new model that might replace junior developers."
    print(f"Routing Post: '{post}'")
    matches = route_post_to_bots(post, threshold=0.25)
    print(f"Matched Bots (Threshold > 0.25): {matches}")
