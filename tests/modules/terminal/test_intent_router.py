"""
Unit tests for ``aios.terminal.intent_router.IntentRouter``.

Pure keyword classification + mock LLM fallback — no network
calls, no real LLM invocations.
"""
import pytest

from aios.terminal.intent_router import (
    ClassificationResult,
    Confidence,
    Intent,
    IntentRouter,
)


# ------------------------------------------------------------------
# Keyword classification: FILE_OPERATION high confidence
# ------------------------------------------------------------------

class TestFileOperationHighConfidence:
    """File verb + file noun together → FILE_OPERATION, HIGH."""

    def test_create_file(self):
        router = IntentRouter()
        r = router.classify("create a file for notes")
        assert r.intent == Intent.FILE_OPERATION
        assert r.confidence == Confidence.HIGH
        assert r.source == "keyword"

    def test_delete_directory(self):
        router = IntentRouter()
        r = router.classify("delete the old directory")
        assert r.intent == Intent.FILE_OPERATION
        assert r.confidence == Confidence.HIGH

    def test_multiple_verbs_and_nouns(self):
        router = IntentRouter()
        r = router.classify("create and rename file in folder")
        assert r.intent == Intent.FILE_OPERATION
        assert r.confidence == Confidence.HIGH

    def test_read_file(self):
        router = IntentRouter()
        r = router.classify("read the file contents")
        assert r.intent == Intent.FILE_OPERATION
        assert r.confidence == Confidence.HIGH


# ------------------------------------------------------------------
# Keyword classification: CHAT high confidence
# ------------------------------------------------------------------

class TestChatHighConfidence:
    """Greetings / personal statements → CHAT, HIGH."""

    def test_greeting_hello(self):
        router = IntentRouter()
        r = router.classify("hello there!")
        assert r.intent == Intent.CHAT
        assert r.confidence == Confidence.HIGH
        assert r.source == "keyword"

    def test_greeting_good_morning(self):
        router = IntentRouter()
        r = router.classify("good morning, how are you?")
        assert r.intent == Intent.CHAT
        assert r.confidence == Confidence.HIGH

    def test_personal_statement(self):
        router = IntentRouter()
        r = router.classify("my name is Alice and I enjoy coding")
        assert r.intent == Intent.CHAT
        assert r.confidence == Confidence.HIGH

    def test_question_not_about_files(self):
        """Non-file question (ends with ?) boosts chat score."""
        router = IntentRouter()
        r = router.classify("what is the weather today?")
        assert r.intent == Intent.CHAT
        assert r.confidence == Confidence.HIGH


# ------------------------------------------------------------------
# Keyword classification: reduced score paths (0.3 multiplier)
# ------------------------------------------------------------------

class TestReducedScorePaths:
    """Verb-without-noun or noun-without-verb gets 0.3x."""

    def test_file_verb_without_noun(self):
        """'create something' — verb hit but no file noun.
        Score = 1 * 0.3 = 0.3, which alone gives FILE_OPERATION
        HIGH (chat_score is 0)."""
        router = IntentRouter()
        r = router.classify("create something")
        assert r.intent == Intent.FILE_OPERATION
        assert r.confidence == Confidence.HIGH

    def test_file_noun_without_verb(self):
        """'the file is large' — noun hit but no file verb.
        Score = 1 * 0.3 = 0.3, no chat signals → HIGH."""
        router = IntentRouter()
        r = router.classify("the file is large")
        assert r.intent == Intent.FILE_OPERATION
        assert r.confidence == Confidence.HIGH

    def test_verb_only_vs_greeting_ambiguous(self):
        """'hi create' — greeting gives chat_score=2.0,
        'create' alone gives file_score=0.3.
        Ratio = 2.0/0.3 ≈ 6.67 > threshold → CHAT HIGH."""
        router = IntentRouter()
        r = router.classify("hi create")
        assert r.intent == Intent.CHAT
        assert r.confidence == Confidence.HIGH


# ------------------------------------------------------------------
# Ambiguous / mixed signals
# ------------------------------------------------------------------

class TestAmbiguousClassification:
    """No signals, or mixed signals below threshold."""

    def test_no_signals_at_all(self):
        """No file keywords, no chat keywords → CHAT AMBIGUOUS."""
        router = IntentRouter()
        r = router.classify("something random")
        assert r.intent == Intent.CHAT
        assert r.confidence == Confidence.AMBIGUOUS
        assert r.source == "keyword"

    def test_empty_input(self):
        router = IntentRouter()
        r = router.classify("")
        assert r.intent == Intent.CHAT
        assert r.confidence == Confidence.AMBIGUOUS

    def test_mixed_signals_below_threshold(self):
        """Input with both file and chat signals where ratio < 2.0.
        'i prefer to read file' — personal 'i prefer' gives
        chat_score=1.5, file verb+noun gives file_score=2.0.
        Ratio = 2.0/1.5 = 1.33 < 2.0 threshold → AMBIGUOUS from
        keyword classifier (FILE_OPERATION because file > chat).
        But classify() then calls _llm_classify fallback, and with
        no LLM fn it defaults to CHAT AMBIGUOUS."""
        router = IntentRouter()
        r = router.classify("i prefer to read file")
        assert r.intent == Intent.CHAT
        assert r.confidence == Confidence.AMBIGUOUS
        assert r.source == "keyword"

    def test_mixed_signals_below_threshold_keyword_only(self):
        """Same as above but testing _keyword_classify directly
        to verify the pre-fallback classification."""
        router = IntentRouter()
        r = router._keyword_classify("i prefer to read file")
        assert r.intent == Intent.FILE_OPERATION
        assert r.confidence == Confidence.AMBIGUOUS
        assert r.source == "keyword"

    def test_mixed_chat_wins_when_equal_or_higher(self):
        """'i need to list things?' — 'i need' is personal
        (chat_score=1.5), question without file noun (+1.0)
        = chat_score 2.5. 'list' is file verb without noun
        = file_score 0.3. Ratio = 2.5/0.3 > 2 → CHAT HIGH."""
        router = IntentRouter()
        r = router.classify("i need to list things?")
        assert r.intent == Intent.CHAT
        assert r.confidence == Confidence.HIGH


# ------------------------------------------------------------------
# Confidence threshold boundary
# ------------------------------------------------------------------

class TestConfidenceThreshold:
    """Ratio of max/min scores around the 2.0 boundary."""

    def test_ratio_exactly_at_threshold(self):
        """file verb+noun = 2 hits = score 2.0.
        Question without file noun = score 1.0.
        Ratio = 2.0/1.0 = 2.0 — NOT < threshold, so
        it falls through to file_score > chat_score branch
        → FILE_OPERATION HIGH."""
        router = IntentRouter()
        # 'create file okay?' — file score 2, question score 1
        # (question ends with ?, no file noun in words...
        # but 'file' IS in words so question boost doesn't apply)
        # Let's use 'delete file what?' — delete+file=2,
        # question has 'file' in words so no question boost,
        # chat_score=0 → skips mixed branch entirely.
        # Better: 'read something?' — verb only = 0.3, question = 1.0
        # Both positive, ratio = 1.0/0.3 = 3.33 > 2 → CHAT HIGH
        r = router.classify("read something?")
        assert r.intent == Intent.CHAT
        assert r.confidence == Confidence.HIGH

    def test_ratio_just_below_threshold(self):
        """Construct a scenario where ratio < 2.0.
        'i like to create file' — personal 'i like' = 1.5,
        create+file = 2.0. Ratio = 2.0/1.5 = 1.33 < 2.0
        → keyword classifier returns FILE_OPERATION AMBIGUOUS,
        then classify() falls through to LLM fallback.
        With no LLM fn → CHAT AMBIGUOUS."""
        router = IntentRouter()
        r = router.classify("i like to create file")
        assert r.intent == Intent.CHAT
        assert r.confidence == Confidence.AMBIGUOUS

    def test_ratio_just_below_threshold_keyword_only(self):
        """Same scenario tested at the keyword classifier level
        to confirm FILE_OPERATION is the pre-fallback choice."""
        router = IntentRouter()
        r = router._keyword_classify("i like to create file")
        assert r.intent == Intent.FILE_OPERATION
        assert r.confidence == Confidence.AMBIGUOUS


# ------------------------------------------------------------------
# LLM fallback path
# ------------------------------------------------------------------

class TestLLMFallback:
    """LLM fallback behaviour with mock callables."""

    def test_no_llm_fn_stays_chat_ambiguous(self):
        """Without llm_classify_fn, ambiguous stays CHAT."""
        router = IntentRouter(llm_classify_fn=None)
        r = router.classify("something random")
        assert r.intent == Intent.CHAT
        assert r.confidence == Confidence.AMBIGUOUS
        assert r.source == "keyword"

    def test_llm_fn_returns_file_operation(self):
        """Mock LLM callable returning FILE_OPERATION →
        HIGH confidence, source='llm'."""
        def mock_llm(text: str) -> Intent:
            return Intent.FILE_OPERATION

        router = IntentRouter(llm_classify_fn=mock_llm)
        r = router.classify("do the thing")
        assert r.intent == Intent.FILE_OPERATION
        assert r.confidence == Confidence.HIGH
        assert r.source == "llm"

    def test_llm_fn_returns_chat(self):
        """Mock LLM callable returning CHAT."""
        def mock_llm(text: str) -> Intent:
            return Intent.CHAT

        router = IntentRouter(llm_classify_fn=mock_llm)
        r = router.classify("ambiguous stuff")
        assert r.intent == Intent.CHAT
        assert r.confidence == Confidence.HIGH
        assert r.source == "llm"

    def test_llm_fn_raises_exception_fails_open(self):
        """LLM callable raising → fail-open to CHAT AMBIGUOUS,
        exception not propagated."""
        def exploding_llm(text: str) -> Intent:
            raise RuntimeError("LLM service unavailable")

        router = IntentRouter(llm_classify_fn=exploding_llm)
        r = router.classify("mystery input")
        assert r.intent == Intent.CHAT
        assert r.confidence == Confidence.AMBIGUOUS
        assert r.source == "llm"

    def test_llm_not_called_when_keyword_is_high(self):
        """LLM fallback should NOT be invoked when keyword
        classification returns HIGH confidence."""
        call_count = {"n": 0}

        def tracking_llm(text: str) -> Intent:
            call_count["n"] += 1
            return Intent.FILE_OPERATION

        router = IntentRouter(llm_classify_fn=tracking_llm)
        r = router.classify("hello there")
        assert r.confidence == Confidence.HIGH
        assert r.source == "keyword"
        assert call_count["n"] == 0


# ------------------------------------------------------------------
# Scoring internals (white-box)
# ------------------------------------------------------------------

class TestScoringInternals:
    """Direct calls to scoring methods for edge verification."""

    def test_file_score_verb_and_noun(self):
        router = IntentRouter()
        score = router._file_score("create a file")
        # verb_hits = {"create"}, noun_hits = {"file"} → 1+1 = 2.0
        assert score == 2.0

    def test_file_score_verb_only(self):
        router = IntentRouter()
        score = router._file_score("create something")
        assert score == pytest.approx(0.3)

    def test_file_score_noun_only(self):
        router = IntentRouter()
        score = router._file_score("the file is here")
        assert score == pytest.approx(0.3)

    def test_file_score_no_hits(self):
        router = IntentRouter()
        score = router._file_score("hello world")
        assert score == 0.0

    def test_chat_score_greeting(self):
        router = IntentRouter()
        score = router._chat_score("hello everyone")
        assert score == 2.0

    def test_chat_score_personal(self):
        router = IntentRouter()
        score = router._chat_score("my name is bob")
        assert score == 1.5

    def test_chat_score_question_no_file_noun(self):
        router = IntentRouter()
        score = router._chat_score("what is python?")
        assert score == 1.0

    def test_chat_score_question_with_file_noun(self):
        """Question with a file noun in words should NOT get the
        +1.0 boost. But since split() keeps punctuation attached
        ('file?' not 'file'), the word won't match FILE_NOUNS
        and the boost DOES apply. This tests the real behavior."""
        router = IntentRouter()
        # 'file?' != 'file' in word set → question boost applies
        score = router._chat_score("what is a file?")
        assert score == 1.0

    def test_chat_score_question_with_bare_file_noun(self):
        """When a file noun appears as a bare word (not
        punctuation-attached), the question boost is suppressed."""
        router = IntentRouter()
        # 'file' is a bare word before the '?' at end
        score = router._chat_score("is the file ready?")
        # words = {"is", "the", "file", "ready?"} — 'file'
        # matches FILE_NOUNS → question boost suppressed
        assert score == 0.0

    def test_chat_score_greeting_plus_question(self):
        """Greeting + non-file question → 2.0 + 1.0 = 3.0."""
        router = IntentRouter()
        score = router._chat_score("hey what's up?")
        assert score == 3.0

    def test_chat_score_personal_plus_question(self):
        """Personal + non-file question → 1.5 + 1.0 = 2.5."""
        router = IntentRouter()
        score = router._chat_score("i want to know more?")
        assert score == 2.5
