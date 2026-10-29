import re
from collections import Counter

from .models import FAQEntry


def _tokenize(text: str):
	return [t for t in re.findall(r"[a-z0-9]+", (text or "").lower()) if len(t) > 2]


def score_faq(entry: FAQEntry, query_tokens: list[str]) -> float:
	blob = " ".join(
		[
			entry.question or "",
			entry.answer or "",
			entry.keywords or "",
		]
	)
	doc_tokens = _tokenize(blob)
	if not doc_tokens or not query_tokens:
		return 0.0

	doc_counts = Counter(doc_tokens)
	overlap = sum(doc_counts[t] for t in query_tokens if t in doc_counts)
	question_bonus = sum(2 for t in query_tokens if t in _tokenize(entry.question))
	return float(overlap + question_bonus)


def answer_question(question: str, *, top_k: int = 3):
	query_tokens = _tokenize(question)
	entries = list(FAQEntry.objects.filter(is_active=True))
	if not entries:
		return {
			"answer": (
				"I don't have FAQ content yet. Please contact support about payments, "
				"custom orders, or delivery."
			),
			"matches": [],
		}

	ranked = sorted(
		((score_faq(entry, query_tokens), entry) for entry in entries),
		key=lambda pair: pair[0],
		reverse=True,
	)
	matches = [
		{
			"id": entry.id,
			"question": entry.question,
			"answer": entry.answer,
			"score": score,
		}
		for score, entry in ranked[:top_k]
		if score > 0
	]

	if not matches:
		return {
			"answer": (
				"I couldn't find a close match. Common topics: 50% deposit payments, "
				"custom crochet requests, delivery timelines, and order status updates."
			),
			"matches": [],
		}

	best = matches[0]
	return {
		"answer": best["answer"],
		"matches": matches,
	}
