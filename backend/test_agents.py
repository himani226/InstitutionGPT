import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from agents.router       import route
from agents.orchestrator import process

# ── Section 1: Routing accuracy (no LLM — fast) ──────────────────────────────
ROUTING_TESTS = [
    # (query,                                          role,     expected_agent)
    ("How do I apply for B.Tech admissions?",          "student", "admissions"),
    ("What scholarship do I get with 86% marks?",      "student", "admissions"),
    ("What subjects are in B.Tech CSE Semester 5?",    "student", "academics"),
    ("When do December end-semester exams begin?",     "student", "academics"),
    ("What is the hostel curfew on weekdays?",         "student", "student"),
    ("How many library books can I borrow?",           "student", "student"),
    ("What is the SCI journal publication incentive?", "faculty", "faculty"),
    ("How many days of maternity leave do I get?",     "faculty", "faculty"),
    ("How do I get an urgent bonafide certificate?",   "admin",   "admin"),
    ("How do I reset my ERP portal password?",         "admin",   "admin"),
]

# ── Section 2: Role-access block verification ─────────────────────────────────
ACCESS_TESTS = [
    # (query,                               role,      blocked_agent)
    ("What is the faculty pay scale?",      "student", "faculty"),
    ("What is the admin procurement rule?", "student", "admin"),
    ("How do student hostels work?",        "faculty", "student"),
]

# ── Section 3: Full pipeline (LLM calls) ──────────────────────────────────────
PIPELINE_TESTS = [
    {"query": "What documents do I need at the time of B.Tech admission?", "role": "student"},
    {"query": "What is the total MBA fee per year?",                        "role": "student"},
    {"query": "When does the mid-semester exam happen in September?",       "role": "student"},
    {"query": "What is the cash reward for a faculty SCI Q1 paper?",       "role": "faculty"},
    {"query": "How long does a bonafide certificate take and what does it cost?", "role": "admin"},
]


if __name__ == "__main__":
    SEP = "=" * 68

    # ── 1. Routing accuracy ──────────────────────────────────────────────
    print(f"\n{SEP}")
    print("  InstitutionGPT — Multi-Agent System Test")
    print(SEP)

    print("\n── SECTION 1: Routing accuracy (no LLM) ──\n")
    correct = 0
    for query, role, expected in ROUTING_TESTS:
        r  = route(query, role=role)
        ok = r["agent"] == expected
        correct += ok
        mark = "✓" if ok else "✗"
        print(f"  {mark}  [{role:8}]  {query:<55}")
        if not ok:
            print(f"       Expected: {expected}  |  Got: {r['agent']}  |  Score: {r['score']}")
        else:
            print(f"       → {r['agent']}  (score: {r['score']})")

    print(f"\n  Accuracy: {correct}/{len(ROUTING_TESTS)}\n")

    # ── 2. Access control ────────────────────────────────────────────────
    print("── SECTION 2: Role-based access control ──\n")
    for query, role, blocked in ACCESS_TESTS:
        r          = route(query, role=role)
        is_blocked = blocked not in r["allowed"]
        mark       = "✓" if is_blocked else "✗"
        print(f"  {mark}  [{role}] '{blocked}' agent correctly blocked: {is_blocked}")
        print(f"       Routed to: {r['agent']} | Allowed: {r['allowed']}")

    # ── 3. Full pipeline ─────────────────────────────────────────────────
    print(f"\n── SECTION 3: Full RAG pipeline ──")
    for i, t in enumerate(PIPELINE_TESTS, 1):
        print(f"\n[Q{i}] [{t['role'].upper()}] {t['query']}")
        print("-" * 68)
        res = process(t["query"], role=t["role"], debug=True)
        print(f"  Agent   : {res['agent']}")
        print(f"  Sources : {', '.join(res['sources'])}")
        print(f"  Scores  : {res['routing']['all_scores']}")
        print(f"\n  Answer:\n{res['answer']}")