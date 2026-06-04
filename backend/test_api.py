"""
Integration tests for the InstitutionGPT API.
Uses FastAPI's TestClient (no server needed — runs in process).
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def section(title: str):
    print(f"\n── {title} ──")


def test_health():
    section("GET /api/health")
    r = client.get("/api/health")
    assert r.status_code == 200
    d = r.json()
    assert d["status"] == "ok"
    assert d["chunks_in_db"] > 0
    print(f"  ✓  status={d['status']}  chunks={d['chunks_in_db']}")


def test_agents():
    section("GET /api/agents")
    r = client.get("/api/agents")
    assert r.status_code == 200
    agents = r.json()
    assert len(agents) == 5
    for a in agents:
        print(f"  ✓  {a['key']:<12}  accessible by: {a['accessible_by']}")


def test_roles():
    section("GET /api/roles")
    r = client.get("/api/roles")
    assert r.status_code == 200
    roles = r.json()
    assert "student" in roles and "faculty" in roles and "admin" in roles
    for role, info in roles.items():
        print(f"  ✓  {role:<10}  agents: {info['agents']}")


def test_chat_student():
    section("POST /api/chat  [student]")
    r = client.post("/api/chat", json={
        "query": "What is the last date to apply for B.Tech admissions?",
        "role":  "student",
        "debug": True,
    })
    assert r.status_code == 200
    d = r.json()
    assert d["answer"]
    assert d["agent"]
    assert d["session_id"]
    print(f"  ✓  agent={d['agent']}")
    print(f"  ✓  sources={d['sources']}")
    print(f"  ✓  routing={d['routing']['all_scores']}")
    print(f"\n  Answer:\n{d['answer'][:300]}...")
    return d["session_id"]


def test_session_continuity(session_id: str):
    section(f"GET /api/session/{session_id}")
    r = client.get(f"/api/session/{session_id}")
    assert r.status_code == 200
    msgs = r.json()["messages"]
    assert len(msgs) == 2             # one user turn + one assistant turn
    print(f"  ✓  {len(msgs)} messages in session")
    print(f"  ✓  user:      {msgs[0]['content'][:60]}...")
    print(f"  ✓  assistant: {msgs[1]['content'][:60]}...")


def test_chat_faculty():
    section("POST /api/chat  [faculty]")
    r = client.post("/api/chat", json={
        "query": "What is the cash reward for publishing in an SCI Q1 journal?",
        "role":  "faculty",
    })
    assert r.status_code == 200
    d = r.json()
    print(f"  ✓  agent={d['agent']}")
    print(f"  ✓  Answer:\n{d['answer'][:300]}...")


def test_chat_admin():
    section("POST /api/chat  [admin]")
    r = client.post("/api/chat", json={
        "query": "How do I get an urgent bonafide certificate?",
        "role":  "admin",
    })
    assert r.status_code == 200
    d = r.json()
    print(f"  ✓  agent={d['agent']}")
    print(f"  ✓  Answer:\n{d['answer'][:300]}...")


def test_invalid_role():
    section("POST /api/chat  [invalid role → 400]")
    r = client.post("/api/chat", json={
        "query": "hello",
        "role":  "hacker",
    })
    assert r.status_code == 400
    print(f"  ✓  Correctly rejected — {r.json()['detail']}")


def test_streaming():
    section("POST /api/chat/stream  [SSE streaming]")
    events = []
    with client.stream("POST", "/api/chat/stream", json={
        "query": "What is the hostel fee per year?",
        "role":  "student",
    }) as r:
        assert r.status_code == 200
        for line in r.iter_lines():
            if line.startswith("data:"):
                import json as _json
                ev = _json.loads(line[5:].strip())
                events.append(ev)
                if ev["type"] == "meta":
                    print(f"  ✓  meta  → agent={ev['agent']}, sources={ev['sources']}")
                elif ev["type"] == "done":
                    print(f"  ✓  done  → {len([e for e in events if e['type']=='token'])} tokens received")

    assert any(e["type"] == "meta"  for e in events)
    assert any(e["type"] == "token" for e in events)
    assert any(e["type"] == "done"  for e in events)


def test_clear_session(session_id: str):
    section(f"DELETE /api/session/{session_id}")
    r = client.delete(f"/api/session/{session_id}")
    assert r.status_code == 200
    print(f"  ✓  {r.json()['message']}")


if __name__ == "__main__":
    print("\n" + "=" * 65)
    print("  InstitutionGPT — API Integration Tests")
    print("=" * 65)

    test_health()
    test_agents()
    test_roles()
    sid = test_chat_student()
    test_session_continuity(sid)
    test_chat_faculty()
    test_chat_admin()
    test_invalid_role()
    test_streaming()
    test_clear_session(sid)

    print("\n" + "=" * 65)
    print("  All tests passed ✓")
    print("=" * 65)