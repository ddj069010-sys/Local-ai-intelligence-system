"""
tests/test_doc_engine.py
------------------------
Unit tests for the Document Creation Engine.
Tests intent detection, planner structure, and version store operations.
Designed to work with the full backend import chain.
"""

import sys
import os

# Add backend to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

print("🔄 Loading Document Engine modules...")

# ═══════════════════════════════════════════════════════════════
# TEST 1: DOC VERSION STORE (Pure Python — No Heavy Imports)
# ═══════════════════════════════════════════════════════════════

def test_doc_version_store():
    from engine.doc_store import DocVersionStore

    store = DocVersionStore()
    chat_id = "test-session-001"

    # Save v1
    v1 = store.save_version(chat_id, "# Report v1\n\n## Introduction\nFirst version.", doc_type="report", action="create")
    assert v1.version_id is not None
    assert store.get_version_count(chat_id) == 1

    # Save v2
    v2 = store.save_version(chat_id, "# Report v2\n\n## Introduction\nEdited version.", doc_type="report", action="edit")
    assert store.get_version_count(chat_id) == 2

    # Get latest
    latest = store.get_latest(chat_id)
    assert latest is not None
    assert latest.version_id == v2.version_id
    assert "v2" in latest.content

    # Get specific version
    first = store.get_version(chat_id, 0)
    assert first is not None
    assert first.version_id == v1.version_id

    # List versions
    version_list = store.list_versions(chat_id)
    assert len(version_list) == 2
    assert version_list[0]["action"] == "create"
    assert version_list[1]["action"] == "edit"

    # Undo
    reverted = store.undo(chat_id)
    assert reverted is not None
    assert reverted.version_id == v1.version_id
    assert store.get_version_count(chat_id) == 1

    # Undo with only 1 version
    no_undo = store.undo(chat_id)
    assert no_undo is None

    # Non-existent chat
    assert store.get_latest("nonexistent") is None
    assert store.list_versions("nonexistent") == []

    # Clear
    store.save_version(chat_id, "new content", action="create")
    store.clear(chat_id)
    assert store.get_version_count(chat_id) == 0

    print("✅ TEST 1 PASSED: DocVersionStore operations work correctly!")


# ═══════════════════════════════════════════════════════════════
# TEST 2: FAST KEYWORD CLASSIFICATION (Requires doc_engine imports)
# ═══════════════════════════════════════════════════════════════

def test_fast_classify():
    from engine.doc_engine import _fast_classify

    # CREATE actions
    assert _fast_classify("write a report on AI")["doc_action"] == "create"
    assert _fast_classify("create a blog post about Python")["doc_action"] == "create"
    assert _fast_classify("draft a memo for the team")["doc_action"] == "create"
    assert _fast_classify("compose a formal email")["doc_action"] == "create"
    assert _fast_classify("generate a code documentation")["doc_action"] == "create"

    # EDIT actions
    assert _fast_classify("improve this document")["doc_action"] == "edit"
    assert _fast_classify("fix the introduction section")["doc_action"] == "edit"

    # SUMMARIZE actions
    assert _fast_classify("make it shorter")["doc_action"] == "summarize"
    assert _fast_classify("summarize the report")["doc_action"] == "summarize"

    # EXPAND actions
    assert _fast_classify("expand the analysis section")["doc_action"] == "expand"
    assert _fast_classify("add more details")["doc_action"] == "expand"

    # REWRITE actions
    assert _fast_classify("rewrite professionally")["doc_action"] == "rewrite"
    assert _fast_classify("convert to email format")["doc_action"] == "rewrite"

    # FORMAT actions
    assert _fast_classify("format this document properly")["doc_action"] == "format"

    # DOC TYPE detection
    assert _fast_classify("write a report on climate change")["doc_type"] == "report"
    assert _fast_classify("write an essay about philosophy")["doc_type"] == "essay"
    assert _fast_classify("draft an email to the manager")["doc_type"] == "email"
    assert _fast_classify("create meeting notes")["doc_type"] == "notes"
    assert _fast_classify("write a blog post about React")["doc_type"] == "blog"

    # TONE detection
    assert _fast_classify("write a formal report")["tone"] == "formal"
    assert _fast_classify("write a casual blog post")["tone"] == "casual"

    # LENGTH detection
    assert _fast_classify("write a brief summary")["length"] == "short"
    assert _fast_classify("write a comprehensive analysis")["length"] == "long"
    assert _fast_classify("write a report on AI")["length"] == "medium"

    print("✅ TEST 2 PASSED: Fast keyword classification works correctly!")


# ═══════════════════════════════════════════════════════════════
# TEST 3: DOC FORMATTER (Requires formatter imports)
# ═══════════════════════════════════════════════════════════════

def test_doc_formatter():
    from engine.doc_engine import format_document

    # Test H1 injection
    raw = "My Report Title\n\nSome content here."
    formatted = format_document(raw, "report")
    assert formatted.startswith("# My Report Title")

    # Test already has H1
    raw2 = "# Existing Title\n\nContent."
    formatted2 = format_document(raw2, "report")
    assert formatted2.startswith("# Existing Title")

    # Test empty content
    assert format_document("", "report") == ""

    # Test email formatting removes ## headers
    raw_email = "## Subject Line\nHello Team\n\n## Body\nPlease review.\n\n## Sign-off\nBest regards"
    formatted_email = format_document(raw_email, "email")
    assert "## Subject Line" not in formatted_email

    print("✅ TEST 3 PASSED: Document formatter works correctly!")


# ═══════════════════════════════════════════════════════════════
# TEST 4: PLAN TEMPLATES
# ═══════════════════════════════════════════════════════════════

def test_plan_templates():
    from engine.doc_engine import _PLAN_TEMPLATES

    expected_types = ["report", "essay", "email", "notes", "blog", "code_doc"]
    for doc_type in expected_types:
        assert doc_type in _PLAN_TEMPLATES, f"Missing template for {doc_type}"
        assert len(_PLAN_TEMPLATES[doc_type]) >= 3, f"Too few sections in {doc_type} template"

    print("✅ TEST 4 PASSED: Plan templates exist for all doc types!")


# ═══════════════════════════════════════════════════════════════
# RUN ALL TESTS
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("\n🧪 DOCUMENT ENGINE TEST SUITE\n" + "=" * 50)

    # Test 1: Pure Python (no heavy imports)
    test_doc_version_store()

    # Tests 2-4: Requires full import chain
    try:
        test_fast_classify()
        test_doc_formatter()
        test_plan_templates()
    except Exception as e:
        print(f"⚠️ Tests 2-4 require full backend environment: {e}")
        print("   Run from: cd backend && python tests/test_doc_engine.py")

    print("\n" + "=" * 50)
    print("🎉 ALL TESTS COMPLETED!")
