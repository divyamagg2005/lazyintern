import unittest

from pipeline.full_scorer import full_score


class TestScorer(unittest.TestCase):
    def test_full_score_runs(self) -> None:
        internship = {
            "role": "AI Intern",
            "description": "We use Python and PyTorch for NLP and LLM work.",
            "location": "Remote",
            "link": "https://example.com/jobs/ai-intern",
        }
        resume = {
            "target_roles": ["AI Intern"],
            "skills": {"languages": ["Python"], "frameworks": ["PyTorch"]},
            "preferred_locations": ["Remote"],
        }
        r = full_score(internship, resume)
        self.assertGreaterEqual(r.score, 0)

