import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).parents[1]


def load_module(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / f'{name}.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


guidance = load_module('guidance')
connection = load_module('connection')


class FakeHost:
    home = Path('/profiles/test')

    def __init__(self, runtime):
        self.result = runtime

    def read(self):
        return {'url': connection.ENDPOINT, 'auth': 'oauth', 'enabled': True}

    def runtime(self):
        return self.result


class DiscoveryTests(unittest.TestCase):
    def test_replaid_request_receives_qualified_skill(self):
        result = guidance.guide_replaid_request('Use Replaid to save a draft', future_field=True)
        self.assertIn('skill_view(name="replaid:social-inbox")', result['context'])
        self.assertIn('draft_reply', result['context'])
        self.assertIn('do not send', result['context'])

    def test_unrelated_requests_are_unchanged(self):
        for message in ['Show Slack messages', 'Read my email', '', None, 'notreplaid']:
            self.assertIsNone(guidance.guide_replaid_request(message))

    def test_saved_config_does_not_claim_runtime_tools_exist(self):
        result = connection.runtime_status(FakeHost({'status': 'configured', 'tools': 0}))
        self.assertTrue(result['configured'])
        self.assertFalse(result['runtime_tools_available'])
        self.assertIn('Restart', result['next_step'])

    def test_runtime_tools_are_reported_separately(self):
        result = connection.runtime_status(FakeHost({'status': 'connected', 'tools': 23}))
        self.assertTrue(result['runtime_tools_available'])
        self.assertEqual(result['runtime_tool_count'], 23)
        self.assertIn('replaid:social-inbox', result['skills'])

    def test_failed_connection_never_claims_tools_are_ready(self):
        result = connection.runtime_status(FakeHost({'status': 'failed', 'tools': 23}))
        self.assertFalse(result['runtime_tools_available'])

    def test_hermes_discovers_loads_skills_and_dispatches_guidance(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            shutil.copytree(ROOT, root / 'plugins/replaid', ignore=shutil.ignore_patterns('.git', '.ci-hermes', '__pycache__'))
            (root / 'config.yaml').write_text('plugins:\n  enabled:\n    - replaid\n')
            script = '''
import json
from hermes_cli.plugins import discover_plugins, invoke_hook
from tools.skills_tool import skills_list, skill_view
from tools.registry import registry
discover_plugins()
names = {skill['name'] for skill in json.loads(skills_list())['skills']}
for name in ['replaid:social-inbox', 'replaid:channel-management', 'replaid:team-and-webhooks']:
    assert name in names, names
    skill = json.loads(skill_view(name))
    assert skill['success'], skill
assert registry.get_entry('replaid_connection_status') is not None
results = invoke_hook('pre_llm_call', user_message='Save a draft in Replaid', session_id='test')
assert any('replaid:social-inbox' in item.get('context', '') for item in results if isinstance(item, dict)), results
assert not invoke_hook('pre_llm_call', user_message='Read Slack', session_id='test')
from hermes_cli.tools_config import _get_platform_tools
from model_tools import get_tool_definitions
from tools.tool_search import dispatch_tool_search
required = {'mcp__replaid__list_conversations', 'mcp__replaid__execute_action'}
for name in required:
    registry.register(name=name, toolset='mcp-replaid', schema={'name': name, 'description': 'Replaid inbox tool', 'parameters': {'type': 'object', 'properties': {}}}, handler=lambda args: '{}')
registry.register_toolset_alias('replaid', 'mcp-replaid')
for platform_tools in [None, ['skills', 'web']]:
    config = {'plugins': {'enabled': ['replaid']}, 'mcp_servers': {'replaid': {'url': 'https://mcp.replaid.pro', 'enabled': True}}}
    if platform_tools is not None:
        config['platform_toolsets'] = {'cli': platform_tools}
    enabled = _get_platform_tools(config, 'cli')
    definitions = get_tool_definitions(enabled_toolsets=sorted(enabled), quiet_mode=True, skip_tool_search_assembly=True)
    names = {tool['function']['name'] for tool in definitions}
    assert required <= names, ('MCP tools hidden by platform filtering', sorted(required - names), sorted(enabled))
    assert 'replaid_connection_status' in names
    result = json.loads(dispatch_tool_search({'queries': sorted(required), 'limit': 5}, current_tool_defs=definitions))
    assert required <= set(result['tools']), result
print('PASS: skill loading, request guidance, platform-filtered MCP tools, and tool search')
'''
            result = subprocess.run([sys.executable, '-c', script], env={**os.environ, 'HERMES_HOME': str(root)}, text=True, capture_output=True, timeout=30)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn('PASS:', result.stdout)


if __name__ == '__main__':
    unittest.main()
