import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from rag.pipeline import ask

TESTS = [
    {
        "label": "Admissions deadline",
        "query": "What is the last date to apply for B.Tech admissions?",
        "role":  "student",
    },
    {
        "label": "Fee query",
        "query": "How much is the B.Tech CSE fee per semester, and are there any scholarships?",
        "role":  "student",
    },
    {
        "label": "Course content",
        "query": "What subjects does a B.Tech CSE student study in Semester 5?",
        "role":  "student",
    },
    {
        "label": "Exam schedule",
        "query": "When do the December end-semester exams begin and what are the rules?",
        "role":  "student",
    },
    {
        "label": "Faculty research incentives",
        "query": "What cash reward does a faculty member get for publishing in an SCI journal?",
        "role":  "faculty",
    },
]

if __name__ == "__main__":
    print("\n" + "=" * 65)
    print("  InstitutionGPT — RAG Pipeline Test")
    print("=" * 65)

    for i, t in enumerate(TESTS, 1):
        print(f"\n[Q{i}] [{t['role'].upper()}] {t['query']}")
        print("-" * 65)
        result = ask(t["query"], role=t["role"])
        print(result["answer"])
        print(f"\n  Sources : {', '.join(result['sources'])}")
        # Show relevance scores of retrieved chunks
        scores = [c['score'] for c in result['retrieved_chunks']]
        print(f"  Scores  : {scores}")