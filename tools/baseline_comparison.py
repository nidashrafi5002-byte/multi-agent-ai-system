import time
import json
import os
import sys
from datetime import datetime
from dotenv import load_dotenv
from groq import Groq

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

from pipelines.research_pipeline import run_research_pipeline
from pipelines.stock_pipeline import run_stock_pipeline
from pipelines.code_pipeline import run_code_pipeline
from pipelines.job_pipeline import run_job_pipeline
from pipelines.general_pipeline import run_general_pipeline

# ─────────────────────────────────────
# BASELINE — Simple Single Agent
# ─────────────────────────────────────
def simple_chatbot(query: str) -> dict:
    """Simple single agent baseline"""
    start = time.time()

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {
                "role": "system",
                "content": "You are a helpful AI assistant."
            },
            {
                "role": "user",
                "content": query
            }
        ]
    )

    end = time.time()
    answer = response.choices[0].message.content.strip()

    return {
        "answer": answer,
        "time": round(end - start, 2),
        "word_count": len(answer.split()),
        "has_structure": False,
        "has_live_data": False,
        "has_citations": False
    }

# ─────────────────────────────────────
# EVALUATOR — Compare outputs
# ─────────────────────────────────────
def evaluate_response(query: str,
                      baseline_response: dict,
                      our_response: str,
                      domain: str) -> dict:
    """Use AI to evaluate both responses"""

    eval_prompt = f"""
    You are an expert evaluator. Compare these two AI responses
    to the same query and score them.

    Query: {query}
    Domain: {domain}

    RESPONSE A (Simple Chatbot):
    {baseline_response['answer'][:500]}...

    RESPONSE B (Multi-Agent System):
    {our_response[:500]}...

    Score each response from 1-10 on:
    1. Completeness (how complete is the answer?)
    2. Structure (how well organized?)
    3. Accuracy (how accurate/relevant?)
    4. Usefulness (how useful for the user?)

    Reply ONLY in this format:
    A_COMPLETENESS: [1-10]
    A_STRUCTURE: [1-10]
    A_ACCURACY: [1-10]
    A_USEFULNESS: [1-10]
    B_COMPLETENESS: [1-10]
    B_STRUCTURE: [1-10]
    B_ACCURACY: [1-10]
    B_USEFULNESS: [1-10]
    WINNER: [A or B]
    REASON: [one line reason]
    """

    eval_response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": eval_prompt}]
    )

    eval_text = eval_response.choices[0].message.content.strip()

    # Parse scores
    scores = {
        "A": {"completeness": 0, "structure": 0,
              "accuracy": 0, "usefulness": 0},
        "B": {"completeness": 0, "structure": 0,
              "accuracy": 0, "usefulness": 0},
        "winner": "B",
        "reason": ""
    }

    for line in eval_text.split("\n"):
        try:
            if "A_COMPLETENESS:" in line:
                scores["A"]["completeness"] = int(
                    line.split(":")[1].strip())
            elif "A_STRUCTURE:" in line:
                scores["A"]["structure"] = int(
                    line.split(":")[1].strip())
            elif "A_ACCURACY:" in line:
                scores["A"]["accuracy"] = int(
                    line.split(":")[1].strip())
            elif "A_USEFULNESS:" in line:
                scores["A"]["usefulness"] = int(
                    line.split(":")[1].strip())
            elif "B_COMPLETENESS:" in line:
                scores["B"]["completeness"] = int(
                    line.split(":")[1].strip())
            elif "B_STRUCTURE:" in line:
                scores["B"]["structure"] = int(
                    line.split(":")[1].strip())
            elif "B_ACCURACY:" in line:
                scores["B"]["accuracy"] = int(
                    line.split(":")[1].strip())
            elif "B_USEFULNESS:" in line:
                scores["B"]["usefulness"] = int(
                    line.split(":")[1].strip())
            elif "WINNER:" in line:
                scores["winner"] = line.split(":")[1].strip()
            elif "REASON:" in line:
                scores["reason"] = line.split(":")[1].strip()
        except:
            pass

    return scores

# ─────────────────────────────────────
# TEST CASES
# ─────────────────────────────────────
TEST_CASES = [
    {
        "query": "What are the latest advancements in LLMs?",
        "domain": "research",
        "pipeline": run_research_pipeline
    },
    {
        "query": "Analyse AAPL stock for me",
        "domain": "stock",
        "pipeline": run_stock_pipeline
    },
    {
        "query": "Who is Elon Musk?",
        "domain": "general",
        "pipeline": run_general_pipeline
    }
]
    
# ─────────────────────────────────────
# MAIN COMPARISON
# ─────────────────────────────────────
def run_comparison():
    print("\n" + "="*60)
    print("   BASELINE COMPARISON STARTED")
    print("="*60)
    print("Comparing: Simple Chatbot vs Multi-Agent System")
    print("="*60)

    all_results = []
    baseline_wins = 0
    our_wins = 0

    for i, test in enumerate(TEST_CASES):
        print(f"\n[{i+1}/{len(TEST_CASES)}] Domain: {test['domain'].upper()}")
        print(f"Query: {test['query'][:60]}...")

        # Baseline response
        print("\n   🤖 Simple Chatbot responding...")
        baseline = simple_chatbot(test['query'])
        print(f"   ✅ Baseline: {baseline['time']}s | "
              f"{baseline['word_count']} words")

        time.sleep(5)

        # Our system response
        print("\n   🚀 Multi-Agent System responding...")
        start = time.time()
        try:
            our_response = test['pipeline'](test['query'])
            our_time = round(time.time() - start, 2)
            our_words = len(str(our_response).split())
            print(f"   ✅ Our System: {our_time}s | {our_words} words")
        except Exception as e:
            our_response = f"Error: {str(e)}"
            our_time = 0
            our_words = 0
            print(f"   ❌ Error: {str(e)[:50]}")

        time.sleep(5)

        # Evaluate
        print("\n   📊 Evaluating responses...")
        scores = evaluate_response(
            test['query'],
            baseline,
            str(our_response),
            test['domain']
        )

        # Calculate averages
        baseline_avg = round(sum(scores["A"].values()) / 4, 2)
        our_avg = round(sum(scores["B"].values()) / 4, 2)

        if scores["winner"] == "B":
            our_wins += 1
            winner_text = "✅ Multi-Agent System"
        else:
            baseline_wins += 1
            winner_text = "⚠️ Simple Chatbot"

        print(f"\n   📈 SCORES:")
        print(f"   Simple Chatbot:      {baseline_avg}/10")
        print(f"   Multi-Agent System:  {our_avg}/10")
        print(f"   Winner: {winner_text}")
        print(f"   Reason: {scores['reason']}")

        result = {
            "domain": test['domain'],
            "query": test['query'][:60],
            "baseline_time": baseline['time'],
            "our_time": our_time,
            "baseline_score": baseline_avg,
            "our_score": our_avg,
            "baseline_words": baseline['word_count'],
            "our_words": our_words,
            "winner": scores['winner'],
            "reason": scores['reason'],
            "detailed_scores": scores
        }

        all_results.append(result)
        time.sleep(8)

    # Final Summary
    print("\n" + "="*60)
    print("   FINAL COMPARISON SUMMARY")
    print("="*60)

    total = len(TEST_CASES)
    our_win_pct = round((our_wins / total) * 100, 1)

    print(f"\n{'Domain':<12} {'Baseline':<12} {'Our System':<12} {'Winner'}")
    print("-"*50)

    total_baseline = 0
    total_ours = 0

    for r in all_results:
        winner = "🏆 Ours" if r['winner'] == "B" else "⚠️ Baseline"
        print(f"{r['domain']:<12} "
              f"{r['baseline_score']:<12} "
              f"{r['our_score']:<12} "
              f"{winner}")
        total_baseline += r['baseline_score']
        total_ours += r['our_score']

    avg_baseline = round(total_baseline / total, 2)
    avg_ours = round(total_ours / total, 2)
    improvement = round(((avg_ours - avg_baseline) / avg_baseline) * 100, 1)

    print(f"\n{'AVERAGE':<12} {avg_baseline:<12} {avg_ours:<12}")
    print(f"\n🏆 Multi-Agent System won: {our_wins}/{total} ({our_win_pct}%)")
    print(f"📈 Average Score Improvement: +{improvement}%")
    print(f"⚡ Simple Chatbot avg time: {round(sum(r['baseline_time'] for r in all_results)/total, 2)}s")
    print(f"🚀 Our System avg time: {round(sum(r['our_time'] for r in all_results)/total, 2)}s")

    # Save report
    report = {
        "timestamp": datetime.now().strftime("%d-%m-%Y %H:%M"),
        "total_tests": total,
        "our_wins": our_wins,
        "baseline_wins": baseline_wins,
        "win_percentage": our_win_pct,
        "avg_baseline_score": avg_baseline,
        "avg_our_score": avg_ours,
        "improvement_percentage": improvement,
        "results": all_results
    }

    with open("tools/baseline_comparison.json", "w") as f:
        json.dump(report, f, indent=2)

    print(f"\n📄 Report saved: tools/baseline_comparison.json")
    print("="*60)

    return report

if __name__ == "__main__":
    run_comparison()