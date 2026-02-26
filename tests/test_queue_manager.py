import unittest


class TestQueueManager(unittest.TestCase):
    def test_import(self) -> None:
        # Just ensure module imports (avoids accidental syntax/import errors)
        import outreach.queue_manager  # noqa: F401

