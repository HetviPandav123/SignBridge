import os
from typing import List
import requests


class WordSuggester:
    """Suggest words using Datamuse API, fallback to local vocab.txt or small builtin list.

    Usage: s = WordSuggester(); s.suggest('pre') -> ['prefix', ...]
    """

    DATAMUSE_URL = "https://api.datamuse.com/sug"

    def __init__(self, vocab_path: str = "vocab.txt", use_api: bool = True):
        self.vocab_path = vocab_path
        self.use_api = use_api and requests is not None
        self.words = []
        # Load local vocab if available (used as fallback)
        if os.path.exists(self.vocab_path):
            try:
                with open(self.vocab_path, "r", encoding="utf-8") as f:
                    for line in f:
                        w = line.strip()
                        if w:
                            self.words.append(w.lower())
            except Exception:
                self.words = []

        # Minimal builtin fallback vocabulary
        if not self.words:
            self.words = [
                "the","be","to","of","and","a","in","that","have","i",
                "you","is","are","hello","thank","please","sorry","yes","no","good",
                "morning","night","love","want","need","help","where","when","who",
                "what","why","how","name","my","your","can","will","do","this"
            ]

    def suggest(self, prefix: str, max_results: int = 4) -> List[str]:
        """Return up to `max_results` suggestions for `prefix`.

        If Datamuse API is reachable and `use_api` is True we'll query it, otherwise
        fall back to local prefix search.
        """
        if not prefix:
            return []
        p = prefix.lower()

        # Try Datamuse first
        if self.use_api:
            try:
                params = {"s": p, "max": max_results}
                resp = requests.get(self.DATAMUSE_URL, params=params, timeout=1.2)
                if resp.status_code == 200:
                    data = resp.json()
                    words = [entry.get('word') for entry in data if entry.get('word')]
                    # Deduplicate & filter prefix just in case
                    seen = set()
                    out = []
                    for w in words:
                        lw = w.lower()
                        if lw.startswith(p) and lw not in seen:
                            seen.add(lw)
                            out.append(lw)
                    if out:
                        return out[:max_results]
            except Exception:
                # Silence network errors and fall back below
                pass

        # Local prefix match fallback
        results = [w for w in self.words if w.startswith(p)]
        # De-duplicate and limit
        seen = set()
        out = []
        for w in results:
            if w not in seen:
                seen.add(w)
                out.append(w)
            if len(out) >= max_results:
                break
        return out


if __name__ == "__main__":
    s = WordSuggester()
    print(s.suggest("th"))
