import json
import subprocess
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).parents[1] / "scripts" / "research_mailbox.py"


class MailboxTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "discussion").mkdir()
        (self.root / "discussion" / "threads.json").write_text('{"threads": []}\n')

    def tearDown(self):
        self.tmp.cleanup()

    def invoke(self, *args):
        return json.loads(subprocess.run(["python3", str(SCRIPT), *args], check=True, capture_output=True, text=True).stdout)

    def test_agent_thread_hands_off_to_user_and_preserves_reply(self):
        opened = self.invoke("open", str(self.root), "--author", "agent", "--title", "Choose model", "--message", "Brief")
        self.assertEqual(opened["thread"]["awaiting"], "user")
        replied = self.invoke("reply", str(self.root), "thread-001", "--author", "user", "--message", "Option A")
        self.assertEqual(replied["thread"]["awaiting"], "agent")
        stored = json.loads((self.root / "discussion" / "threads.json").read_text())
        self.assertEqual([item["author"] for item in stored["threads"][0]["messages"]], ["agent", "user"])
