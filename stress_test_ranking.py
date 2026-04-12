import asyncio
import sys
import os
import time
import json
import logging

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from engine.utils import get_embedding, cluster_and_rerank, cosine_similarity

# 🎯 MOCK DATA (10 Chunks: 3 High Signal, 3 Low Signal, 4 Noise)
CHUNKS = [
    # HIGH SIGNAL
    "Interest rates in Berlin for 2024 have increased by 2.5%, leading to a slowdown in residential real estate sales in Mitte and Charlottenburg.",
    "Mortgage costs for commercial property in Berlin are at a 10-year high, causing developers to pause construction projects in the city center.",
    "Data from Berlin state statistics show that interest rate hikes have forced many first-time buyers into the rental market, driving up rent by 12%.",
    
    # LOW SIGNAL (Germany general)
    "The European Central Bank is considering lowering interest rates later this year for the entire Eurozone, including Germany.",
    "Real estate investment in Munich and Hamburg remains stable despite fluctuating market conditions across Western Europe.",
    "German economic growth is projected to be 0.5% in 2024, with mixed performance across the industrial and service sectors.",
    
    # NOISE (Completely unrelated)
    "Baking the perfect sourdough bread requires a starter that is well-fed and kept at a temperature of exactly 22 degrees Celsius.",
    "The weather in Tokyo this week will be mostly sunny with the cherry blossoms expected to reach peak bloom on Thursday.",
    "Quantum computing companies are seeing increased venture capital interest as new qubit stability milestones are being achieved.",
    "Modern landscape architecture often emphasizes native plant species and sustainable irrigation techniques to preserve local biodiversity."
]

QUERY = "How do interest rate changes impact real estate prices and buyer behavior in Berlin?"

async def run_stress_test():
    print("🧠 [SYSTEM] Initializing Search Ranking Stress Test...")
    print(f"📡 [QUERY] \"{QUERY}\"")
    print(f"📊 [DATA] Processing {len(CHUNKS)} mock web chunks (Heterogeneous text)...")
    
    start_time = time.time()
    
    # 1. Get Query Embedding
    query_emb = await get_embedding(QUERY)
    if not query_emb:
        print("❌ [ERROR] Could not get query embedding. Is Ollama running?")
        return

    # 2. Get Chunk Embeddings (Parallel simulation)
    print("⚡ [EMBEDDING] Generating vectors for 10 nodes...")
    tasks = [get_embedding(c) for c in CHUNKS]
    embeddings = await asyncio.gather(*tasks)
    
    emb_time = time.time()
    print(f"⏱️ [LATENCY] Vector generation took {emb_time - start_time:.2f}s")
    
    # 3. Run Ranking
    print("🔍 [RANKING] Applying Cosine Similarity + Diversification Cluster Filter...")
    ranked_chunks = cluster_and_rerank(
        chunks=CHUNKS, 
        embeddings=embeddings, 
        query_emb=query_emb, 
        query_text=QUERY, 
        top_n=3
    )
    
    rank_time = time.time()
    print(f"⏱️ [LATENCY] Reranking & Diversity filter took {rank_time - emb_time:.4f}s")
    
    # 4. Results Verification
    print("\n" + "="*60)
    print("🏆 TOP 3 RESEARCH CHUNKS (EXTRACTED SIGNAL)")
    print("="*60)
    
    success_count = 0
    for i, chunk in enumerate(ranked_chunks):
        is_hit = "Berlin" in chunk and "interest" in chunk.lower()
        marker = "✅ [HIT]" if is_hit else "❌ [MISS/NOISE]"
        if is_hit: success_count += 1
        print(f"{i+1}. {marker} {chunk[:120]}...")

    print("="*60)
    print(f"🎯 [ACCURACY] {success_count}/3 High-Signal Chunks detected.")
    print(f"🕒 [TOTAL TIME] {rank_time - start_time:.2f}s")
    
    if success_count == 3:
        print("\n✅ [VERDICT] STRESS TEST PASSED: Search ranking system successfully isolated semantic signals from noise.")
    else:
        print("\n⚠️ [VERDICT] STRESS TEST PARTIAL: Check redundancy thresholds.")

if __name__ == "__main__":
    asyncio.run(run_stress_test())
