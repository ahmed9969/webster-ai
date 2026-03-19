import json
import os
import math
from pathlib import Path

def cosine_similarity(vec1, vec2):
    """Calculate cosine similarity between two vectors"""
    dot_product = sum(a * b for a, b in zip(vec1, vec2))
    magnitude1 = math.sqrt(sum(a * a for a in vec1))
    magnitude2 = math.sqrt(sum(b * b for b in vec2))
    if magnitude1 == 0 or magnitude2 == 0:
        return 0
    return dot_product / (magnitude1 * magnitude2)

def get_embedding(text, client):
    """Get embedding from Anthropic via a simple keyword approach"""
    # Since Anthropic doesn't have embeddings API directly,
    # we use TF-IDF style simple vectorization
    return simple_vectorize(text)

def simple_vectorize(text, vocab_size=1000):
    """Simple TF-IDF style vectorization"""
    import re
    # Clean and tokenize
    words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
    
    # Remove common stopwords
    stopwords = {'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 
                 'can', 'had', 'her', 'was', 'one', 'our', 'out', 'day',
                 'get', 'has', 'him', 'his', 'how', 'its', 'may', 'new',
                 'now', 'old', 'see', 'two', 'who', 'boy', 'did', 'this',
                 'that', 'with', 'have', 'from', 'they', 'will', 'been',
                 'said', 'each', 'which', 'their', 'time', 'there', 'use'}
    
    words = [w for w in words if w not in stopwords]
    
    # Create word frequency dict
    freq = {}
    for word in words:
        freq[word] = freq.get(word, 0) + 1
    
    return freq

class VectorStore:
    def __init__(self, store_path="data/vector_store.json"):
        self.store_path = store_path
        self.chunks = []
        self.load()
    
    def load(self):
        """Load existing vector store if it exists"""
        if Path(self.store_path).exists():
            with open(self.store_path, 'r', encoding='utf-8') as f:
                self.chunks = json.load(f)
            print(f"Loaded {len(self.chunks)} chunks from vector store")
        else:
            print("No existing vector store found, will create new one")
    
    def save(self):
        """Save vector store to disk"""
        os.makedirs(os.path.dirname(self.store_path), exist_ok=True)
        with open(self.store_path, 'w', encoding='utf-8') as f:
            json.dump(self.chunks, f, ensure_ascii=False, indent=2)
        print(f"Saved {len(self.chunks)} chunks to vector store")
    
    def add_chunks(self, chunks):
        """Add document chunks to the store"""
        for chunk in chunks:
            vector = simple_vectorize(chunk["content"])
            self.chunks.append({
                "source": chunk["source"],
                "content": chunk["content"],
                "chunk_id": chunk["chunk_id"],
                "vector": vector
            })
        self.save()
        print(f"Added {len(chunks)} chunks to vector store")
    
    def search(self, query, top_k=5):
        """Search for most relevant chunks"""
        if not self.chunks:
            return []
        
        query_vector = simple_vectorize(query)
        
        scores = []
        for i, chunk in enumerate(self.chunks):
            chunk_vector = chunk.get("vector", {})
            
            # Calculate similarity using shared words
            shared_words = set(query_vector.keys()) & set(chunk_vector.keys())
            if not shared_words:
                score = 0
            else:
                # TF-IDF style scoring
                score = sum(
                    query_vector[w] * chunk_vector[w] 
                    for w in shared_words
                )
                # Normalize by length
                query_len = math.sqrt(sum(v**2 for v in query_vector.values()))
                chunk_len = math.sqrt(sum(v**2 for v in chunk_vector.values()))
                if query_len > 0 and chunk_len > 0:
                    score = score / (query_len * chunk_len)
            
            scores.append((score, i))
        
        # Sort by score descending
        scores.sort(reverse=True, key=lambda x: x[0])
        
        # Return top k results
        results = []
        for score, idx in scores[:top_k]:
            if score > 0:
                results.append({
                    "content": self.chunks[idx]["content"],
                    "source": self.chunks[idx]["source"],
                    "score": score
                })
        
        return results
    
    def is_empty(self):
        return len(self.chunks) == 0
