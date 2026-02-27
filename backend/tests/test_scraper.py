import unittest

from scraper.extractor import extract_internships_from_html


class TestScraper(unittest.TestCase):
    def test_extractor_finds_intern_links(self) -> None:
        html = """
        <html><body>
          <a href="/jobs/ml-intern">ML Intern</a>
          <a href="/about">About</a>
        </body></html>
        """
        items = extract_internships_from_html(html, source_url="https://acme.com")
        self.assertGreaterEqual(len(items), 1)
        self.assertIn("intern", items[0]["role"].lower())

