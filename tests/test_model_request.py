import json
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch
import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import generate_cards as cards


class ModelRequestTests(unittest.TestCase):
    def test_terra_medium_request_and_result(self):
        def post(url, **kwargs):
            self.assertEqual(url, "https://mo.monond.com/v1/chat/completions")
            self.assertEqual(kwargs["json"]["model"], "gpt-5.6-terra")
            self.assertEqual(kwargs["json"]["reasoning_effort"], "medium")
            response = requests.Response()
            response.status_code = 200
            response._content = json.dumps({"choices": [{"message": {"content": '{"items":[]}'}}]}).encode()
            return response
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test", "OPENAI_BASE_URL": "https://mo.monond.com/v1/", "OPENAI_MODEL": "gpt-5.6-terra", "OPENAI_REASONING_EFFORT": "medium"}), patch.object(cards.requests, "post", side_effect=post):
            self.assertEqual(cards.ask_model([]), {"items": []})


if __name__ == "__main__":
    unittest.main()
