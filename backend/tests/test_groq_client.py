import unittest

from pipeline.groq_client import generate_draft


class TestGroqClient(unittest.TestCase):
    def test_generate_draft_has_fields(self) -> None:
        lead = {"email": "hr@example.com", "recruiter_name": "Hiring Team"}
        internship = {"company": "Acme", "role": "AI Intern", "description": ""}
        resume = {"name": "Divyam", "skills": {"languages": ["Python"]}, "projects": []}
        d = generate_draft(lead, internship, resume)
        self.assertTrue(d.subject)
        self.assertTrue(d.body)
        self.assertTrue(d.followup_body)

