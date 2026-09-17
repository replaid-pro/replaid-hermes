import copy
import importlib.util
import os
import shutil
import subprocess
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('replaid_connection', Path(__file__).parents[1] / 'connection.py')
connection = importlib.util.module_from_spec(spec)
spec.loader.exec_module(connection)

GOOD = {'url': connection.ENDPOINT, 'auth': 'oauth', 'enabled': True}
TOOLS = [('list_conversations', ''), ('get_conversation_context', '')]


class Host:
    def __init__(self, config=None):
        self.home = Path('/profiles/customer')
        self.config = copy.deepcopy(config)
        self.saves = 0
        self.calls = 0
        self.tools = TOOLS
        self.failure = False
        self.drop_save = False

    def read(self):
        return copy.deepcopy(self.config)

    def save(self, config):
        self.saves += 1
        if not self.drop_save:
            self.config = copy.deepcopy(config)

    def probe(self, config, interactive=False):
        self.calls += 1
        assert self.config == config, 'Connection must be saved before OAuth'
        if self.failure:
            raise RuntimeError('secret OAuth details')
        return self.tools


class SetupTests(unittest.TestCase):
    def test_saves_before_oauth(self):
        host = Host()
        self.assertEqual(connection.setup(host), 2)
        self.assertEqual(host.config, GOOD)

    def test_existing_connection_is_not_rewritten(self):
        config = {**GOOD, 'oauth': {'client_id': 'existing'}, 'tools': {'exclude': ['execute_action']}}
        host = Host(config)
        self.assertEqual(connection.setup(host), 2)
        self.assertEqual(host.saves, 0)
        self.assertEqual(host.config, config)

    def test_failed_oauth_keeps_saved_entry_and_redacts_error(self):
        host = Host()
        host.failure = True
        with self.assertRaises(connection.SetupError) as raised:
            connection.setup(host)
        self.assertNotIn('secret', str(raised.exception))
        self.assertEqual(host.config, GOOD)

    def test_dropped_save_cannot_report_success(self):
        host = Host()
        host.drop_save = True
        with self.assertRaises(connection.SetupError):
            connection.setup(host)
        self.assertEqual(host.calls, 0)

    def test_refuses_conflicting_or_disabled_connections(self):
        for change in [{'url':'https://other.example'}, {'auth':'header'}, {'enabled':False}, {'headers':{'Authorization':'secret'}}, {'command':'some-command'}]:
            with self.subTest(change=change):
                host = Host({**GOOD, **change})
                with self.assertRaises(connection.SetupError):
                    connection.setup(host)
                self.assertEqual(host.saves, 0)
                self.assertEqual(host.calls, 0)

    def test_respects_tool_restrictions(self):
        for filters in [{'include':[]}, {'include':['list_conversations']}, {'exclude':['get_conversation_context']}]:
            with self.subTest(filters=filters):
                host = Host({**GOOD, 'tools':filters})
                with self.assertRaises(connection.SetupError):
                    connection.setup(host)
                self.assertEqual(host.saves, 0)

    def test_missing_inbox_tools_fail(self):
        host = Host(GOOD)
        host.tools = [('unrelated', '')]
        with self.assertRaises(connection.SetupError):
            connection.check(host)

    def test_status_does_not_connect_or_write(self):
        host = Host()
        result = connection.status(host)
        self.assertFalse(result['configured'])
        self.assertEqual(result['profile'], 'customer')
        self.assertIn('HERMES_HOME=/profiles/customer', result['setup_command'])
        self.assertEqual((host.calls,host.saves), (0,0))

    def test_configured_status_does_not_claim_oauth_verified(self):
        result = connection.status(Host(GOOD))
        self.assertTrue(result['configured'])
        self.assertIn('does not verify OAuth', result['message'])

    def test_clean_profile_discovers_plugin_and_reports_missing_connection(self):
        import yaml
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source = Path(__file__).parents[1]
            shutil.copytree(source, root / 'plugins' / 'replaid', ignore=shutil.ignore_patterns('.git', '.ci-hermes', '__pycache__'))
            config = {'plugins': {'enabled': ['replaid']}}
            (root / 'config.yaml').write_text(yaml.safe_dump(config))
            result = subprocess.run(
                ['hermes', 'replaid', 'status'],
                env={**os.environ, 'HERMES_HOME': str(root)},
                text=True, capture_output=True, timeout=30,
            )
            self.assertEqual(result.returncode, 1, result.stderr)
            self.assertIn('not configured', result.stdout)
            self.assertIn(str(root), result.stdout)
            self.assertNotIn('mcp_servers', yaml.safe_load((root / 'config.yaml').read_text()))
            self.assertFalse((root / 'mcp-tokens').exists())

    def test_real_hermes_persistence_keeps_other_servers(self):
        import yaml
        with tempfile.TemporaryDirectory() as folder, patch.dict(os.environ, {'HERMES_HOME':folder}):
            path = Path(folder) / 'config.yaml'
            original = {'mcp_servers':{'other':{'url':'https://example.org/mcp'}}, 'plugins':{'enabled':['replaid']}}
            path.write_text(yaml.safe_dump(original))
            host = connection.HermesHost()
            with patch.object(host, 'probe', return_value=TOOLS):
                self.assertEqual(connection.setup(host), 2)
            saved = yaml.safe_load(path.read_text())
            self.assertEqual(saved['mcp_servers']['other'], original['mcp_servers']['other'])
            self.assertEqual(saved['mcp_servers']['replaid'], GOOD)
            self.assertEqual(saved['plugins'], original['plugins'])


if __name__ == '__main__':
    unittest.main()
