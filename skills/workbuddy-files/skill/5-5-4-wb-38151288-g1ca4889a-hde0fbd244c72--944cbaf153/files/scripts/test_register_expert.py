#!/usr/bin/env python3
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import register_expert


class RegisterExpertTest(unittest.TestCase):
    def setUp(self):
        self.original_session_env = os.environ.get(register_expert.SESSION_ID_ENV_VAR)
        os.environ.pop(register_expert.SESSION_ID_ENV_VAR, None)

    def tearDown(self):
        if self.original_session_env is None:
            os.environ.pop(register_expert.SESSION_ID_ENV_VAR, None)
        else:
            os.environ[register_expert.SESSION_ID_ENV_VAR] = self.original_session_env

    @staticmethod
    def create_expert_dir(root: Path, name: str = 'test-designer') -> Path:
        expert_dir = root / 'plugins' / name
        (expert_dir / '.codebuddy-plugin').mkdir(parents=True)
        (expert_dir / 'agents').mkdir()
        (expert_dir / '.codebuddy-plugin' / 'plugin.json').write_text(json.dumps({
            'name': name,
            'description': 'Test designer expert',
            'expertType': 'agent',
            'displayName': {'zh': '测试专家', 'en': 'Test Designer'},
        }), encoding='utf-8')
        (expert_dir / 'agents' / f'{name}.md').write_text('You are a test designer.', encoding='utf-8')
        return expert_dir

    def test_register_uses_codebuddy_session_id_env_when_arg_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            marketplace_dir = Path(tmp)
            expert_dir = self.create_expert_dir(marketplace_dir)

            self.assertTrue(register_expert.register_expert(
                expert_dir,
                marketplace_dir,
                register_expert.get_session_id(None),
            ))
            self.assertFalse((expert_dir / '.created-by-session').exists())

            os.environ['CODEBUDDY_SESSION_ID'] = 'session-from-env'

            self.assertTrue(register_expert.register_expert(
                expert_dir,
                marketplace_dir,
                register_expert.get_session_id(None),
            ))
            self.assertEqual((expert_dir / '.created-by-session').read_text(encoding='utf-8'), 'session-from-env')

    def test_explicit_session_id_overrides_env(self):
        os.environ['CODEBUDDY_SESSION_ID'] = 'session-from-env'

        self.assertEqual(register_expert.get_session_id(' explicit-session '), 'explicit-session')

    def test_unexpanded_session_id_falls_back_to_env(self):
        os.environ['CODEBUDDY_SESSION_ID'] = 'session-from-env'

        self.assertEqual(register_expert.get_session_id('${CODEBUDDY_SESSION_ID}'), 'session-from-env')
        self.assertEqual(register_expert.get_session_id('$CODEBUDDY_SESSION_ID'), 'session-from-env')

    def test_blank_session_id_falls_back_to_env(self):
        os.environ['CODEBUDDY_SESSION_ID'] = 'session-from-env'

        self.assertEqual(register_expert.get_session_id('   '), 'session-from-env')


if __name__ == '__main__':
    unittest.main()
