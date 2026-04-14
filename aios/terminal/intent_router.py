"""Intent classification for terminal input routing.

Provides a two-stage classifier (keyword heuristic + LLM
fallback) that determines whether user input is a chat
message or a file operation request.
"""

from dataclasses import dataclass
from enum import Enum
from cerebrum.llm.apis import llm_chat


class Intent(Enum):
    CHAT = "chat"
    FILE_OPERATION = "file_operation"


class Confidence(Enum):
    HIGH = "high"
    AMBIGUOUS = "ambiguous"


@dataclass
class ClassificationResult:
    intent: Intent
    confidence: Confidence
    source: str  # "keyword" or "llm"


class IntentRouter:
    """Two-stage intent classifier: keyword heuristic
    with LLM fallback."""

    # Confidence threshold: ratio of file-score to
    # chat-score (or vice versa) must exceed this to
    # be considered HIGH confidence.
    CONFIDENCE_THRESHOLD = 2.0

    FILE_VERBS = {
        "create", "write", "delete", "list", "read",
        "rollback", "share", "mount", "rename", "move",
        "copy", "remove",
    }
    FILE_NOUNS = {
        "file", "files", "directory", "directories",
        "folder", "folders", "path", "paths",
    }
    CHAT_GREETINGS = {
        "hello", "hi", "hey", "greetings",
        "good morning", "good afternoon",
        "good evening", "howdy",
    }
    CHAT_PERSONAL = {
        "my name is", "i like", "i prefer",
        "i am", "i'm", "i enjoy", "i love",
        "i hate", "i want", "i need",
    }

    def __init__(
        self,
        llm_classify_fn=None,
    ):
        """
        Args:
            llm_classify_fn: Optional callable
                (str) -> Intent for LLM fallback.
                If None, ambiguous inputs default to
                Intent.CHAT.
        """
        self.llm_classify_fn = llm_classify_fn

    def classify(self, user_input: str) -> ClassificationResult:
        """Classify user input as chat or file operation.

        Runs keyword heuristic first. Falls back to LLM
        classifier when confidence is ambiguous.
        """
        result = self._keyword_classify(user_input)
        if result.confidence == Confidence.HIGH:
            return result
        return self._llm_classify(user_input)

    def _keyword_classify(
        self, user_input: str,
    ) -> ClassificationResult:
        """Rule-based classification using keyword
        pattern matching and confidence scoring."""
        text = user_input.lower().strip()
        file_score = self._file_score(text)
        chat_score = self._chat_score(text)

        if file_score == 0 and chat_score == 0:
            return ClassificationResult(
                Intent.CHAT, Confidence.AMBIGUOUS, "keyword",
            )

        if file_score > 0 and chat_score > 0:
            ratio = max(file_score, chat_score) / max(
                min(file_score, chat_score), 0.1,
            )
            if ratio < self.CONFIDENCE_THRESHOLD:
                return ClassificationResult(
                    Intent.CHAT
                    if chat_score >= file_score
                    else Intent.FILE_OPERATION,
                    Confidence.AMBIGUOUS,
                    "keyword",
                )

        if file_score > chat_score:
            return ClassificationResult(
                Intent.FILE_OPERATION,
                Confidence.HIGH,
                "keyword",
            )
        return ClassificationResult(
            Intent.CHAT, Confidence.HIGH, "keyword",
        )

    def _file_score(self, text: str) -> float:
        """Score how likely the input is a file operation.

        Requires at least one file verb AND one file noun
        for a positive score. Individual matches without
        the other category score lower.
        """
        words = set(text.split())
        verb_hits = words & self.FILE_VERBS
        noun_hits = words & self.FILE_NOUNS
        score = 0.0
        if verb_hits and noun_hits:
            score = len(verb_hits) + len(noun_hits)
        elif verb_hits:
            score = len(verb_hits) * 0.3
        elif noun_hits:
            score = len(noun_hits) * 0.3
        return score

    def _chat_score(self, text: str) -> float:
        """Score how likely the input is conversational."""
        score = 0.0
        # Greeting match
        for greeting in self.CHAT_GREETINGS:
            if text.startswith(greeting):
                score += 2.0
                break
        # Personal info match
        for pattern in self.CHAT_PERSONAL:
            if pattern in text:
                score += 1.5
                break
        # Question not about files
        if text.endswith("?"):
            words = set(text.split())
            if not (words & self.FILE_NOUNS):
                score += 1.0
        return score

    def _llm_classify(
        self, user_input: str,
    ) -> ClassificationResult:
        """LLM-based fallback classification."""
        if self.llm_classify_fn is None:
            return ClassificationResult(
                Intent.CHAT, Confidence.AMBIGUOUS, "keyword",
            )
        try:
            intent = self.llm_classify_fn(user_input)
            return ClassificationResult(
                intent, Confidence.HIGH, "llm",
            )
        except Exception:
            # Fail-open to chat
            return ClassificationResult(
                Intent.CHAT, Confidence.AMBIGUOUS, "llm",
            )


LLM_CLASSIFY_SYSTEM_PROMPT = """\
You are an intent classifier for a terminal application.
Classify the user's message into exactly one category:

- "chat": conversational messages, greetings, questions \
about general topics, personal information sharing, \
opinion requests, or anything not related to file \
system operations.
- "file_operation": requests to create, read, write, \
delete, list, rename, move, copy, rollback, share, \
or mount files, directories, or paths.

Respond with ONLY the category name, nothing else.
No explanation, no punctuation, no quotes.
"""


def build_llm_classify_fn(agent_name, base_url=None):
    """Build an LLM classification callable for the
    IntentRouter.

    Returns a function (str) -> Intent that sends the
    user input to the LLM with the classification prompt.
    """
    def classify(user_input: str) -> Intent:
        response = llm_chat(
            agent_name=agent_name,
            messages=[
                {"role": "system",
                 "content": LLM_CLASSIFY_SYSTEM_PROMPT},
                {"role": "user", "content": user_input},
            ],
            **({"base_url": base_url} if base_url else {}),
        )
        raw = str(
            response.get("response", "")
        ).strip().lower()
        # Extract the response_message if present
        if hasattr(raw, "response_message"):
            raw = raw.response_message.strip().lower()
        if "file" in raw:
            return Intent.FILE_OPERATION
        return Intent.CHAT

    return classify
