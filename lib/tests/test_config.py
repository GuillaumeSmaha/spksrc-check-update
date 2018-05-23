# -*- coding: utf-8 -*-

import unittest
from lib import config
from lib.config import Config, convert_duration


class TestConfig(unittest.TestCase):
    """Config integration test"""

    def setUp(self):
        Config.configs_cached = {}

    def test_get_keys(self):
        """Test case: Get keys config
        """
        config.configs = {
            'port': {
                'description': 'Port number',
                'type': int,
                'default': 8080
            },
            'title': {
                'description': 'Title',
                'type': str
            }
        }

        self.assertEqual(sorted(list(Config.get_keys())), ['port', 'title'])

    def test_get(self):
        """Test case: Get a config value
        """
        config.configs = {
            'title': {
                'description': 'Title'
            }
        }

        self.assertIsNone(Config.get('title'))
        self.assertEqual(Config.get('title', 'default'), 'default')

        Config.set('title', 'Great')
        self.assertEqual(Config.get('title'), 'Great')
        self.assertEqual(Config.get('title', 'default'), 'Great')

    def test_get_return_default(self):
        """Test case: Get a config value having a default value
        """
        config.configs = {
            'title': {
                'description': 'Title',
                'default': ''
            }
        }

        self.assertEqual(Config.get('title'), '')

        Config.set('title', 'Great')
        self.assertEqual(Config.get('title'), 'Great')

    def test_get_str(self):
        """Test case for config using a cast to str
        """
        config.configs = {
            'title': {
                'description': 'Title',
                'type': str
            }
        }

        self.assertIsNone(Config.get('title'))

        Config.set('title', 100)
        self.assertNotEqual(Config.get('title'), 100)
        self.assertEqual(Config.get('title'), '100')

    def test_get_int(self):
        """Test case for config using a cast to int
        """
        config.configs = {
            'port': {
                'description': 'Port number',
                'default': 8080,
                'type': int
            }
        }

        self.assertEqual(Config.get('port'), 8080)

        Config.set('port', 1234)
        self.assertEqual(Config.get('port'), 1234)

        Config.set('port', '6443')
        self.assertNotEqual(Config.get('port'), '6443')
        self.assertEqual(Config.get('port'), 6443)

    def test_get_default(self):
        """Test case: Get default values
        """
        config.configs = {
            'port': {
                'description': 'Port number',
                'type': int,
                'default': 8080
            },
            'title': {
                'description': 'Title',
                'type': str
            }
        }

        self.assertEqual(Config.get('port'), 8080)

        Config.set('port', 1234)
        self.assertEqual(Config.get('port'), 1234)

        self.assertEqual(Config.get_default('port'), 8080)

        self.assertIsNone(Config.get('title'))

        Config.set('title', '1234')
        self.assertEqual(Config.get('title'), '1234')

        self.assertIsNone(Config.get_default('title'))
        self.assertEqual(Config.get_default('title', 'empty'), 'empty')

    def test_get_unknow_key(self):
        """Test case: Get unknow key
        """
        config.configs = {
        }

        self.assertIsNone(Config.get('unknow'))
        self.assertIsNone(Config.get_default('unknow'))

    def test_add_new_key(self):
        """Test case: Add a new config key
        """
        config.configs = {
            'port': {
                'description': 'Port number',
                'type': int,
                'default': 8080
            },
            'title': {
                'description': 'Title',
                'type': str
            }
        }

        self.assertEqual(sorted(list(Config.get_keys())), ['port', 'title'])

        Config.set('new-key', 'test')

        self.assertIsNone(Config.get_default('new-key'))
        self.assertEqual(Config.get_default('new-key', 'nada'), 'nada')

        self.assertEqual(Config.get('new-key'), 'test')

        self.assertEqual(sorted(list(Config.get_keys())), ['new-key', 'port', 'title'])

    def test_get_with_var(self):
        """Test case for config using variable in value
        """
        config.configs = {
            'work_dir': {
                'description': 'Working directory',
                'default': 'work',
                'type': str
            },
            'git_dir': {
                'description': 'Git directory',
                'default': '%work_dir%/git',
                'type': str
            }
        }

        self.assertEqual(Config.get('work_dir'), 'work')
        self.assertEqual(Config.get('git_dir'), 'work/git')

        Config.set('work_dir', 'my-work')

        self.assertEqual(Config.get('work_dir'), 'my-work')
        self.assertEqual(Config.get('git_dir'), 'my-work/git')
        self.assertEqual(Config.get_default('work_dir'), 'work')
        self.assertEqual(Config.get_default('git_dir'), 'work/git')

        Config.set('git_dir', 'git')

        self.assertEqual(Config.get('work_dir'), 'my-work')
        self.assertEqual(Config.get('git_dir'), 'git')
        self.assertEqual(Config.get_default('work_dir'), 'work')
        self.assertEqual(Config.get_default('git_dir'), 'work/git')

        Config.set('git_dir', 'git/%work_dir%')

        self.assertEqual(Config.get('work_dir'), 'my-work')
        self.assertEqual(Config.get('git_dir'), 'git/my-work')

    def test_get_with_var_multiple(self):
        """Test case for config using mutiple variables in value
        """
        config.configs = {
            'user': {
                'description': 'User',
                'default': '',
                'type': str
            },
            'mount_dir': {
                'description': 'Mount directory',
                'default': '/mnt',
                'type': str
            },
            'work_dir': {
                'description': 'Working directory',
                'default': '%mount_dir%/home/%user%/work',
                'type': str
            },
            'git_dir': {
                'description': 'Git directory',
                'default': '%work_dir%/git',
                'type': str
            }
        }

        self.assertEqual(Config.get('user'), '')
        Config.set('user', 'guillaume_smaha')
        self.assertEqual(Config.get('user'), 'guillaume_smaha')
        self.assertEqual(Config.get('mount_dir'), '/mnt')

        self.assertEqual(Config.get('work_dir'), '/mnt/home/guillaume_smaha/work')
        self.assertEqual(Config.get('git_dir'), '/mnt/home/guillaume_smaha/work/git')

        Config.set('work_dir', '%mount_dir%/home/%user%/my-work')

        self.assertEqual(Config.get('work_dir'), '/mnt/home/guillaume_smaha/my-work')
        self.assertEqual(Config.get('git_dir'), '/mnt/home/guillaume_smaha/my-work/git')
        self.assertEqual(Config.get_default('work_dir'), '/mnt/home//work')
        self.assertEqual(Config.get_default('git_dir'), '/mnt/home//work/git')

        Config.set('git_dir', 'git')

        self.assertEqual(Config.get('work_dir'), '/mnt/home/guillaume_smaha/my-work')
        self.assertEqual(Config.get('git_dir'), 'git')

        Config.set('git_dir', '%mount_dir%/home/%user%/git/my-work')

        self.assertEqual(Config.get('work_dir'), '/mnt/home/guillaume_smaha/my-work')
        self.assertEqual(Config.get('git_dir'), '/mnt/home/guillaume_smaha/git/my-work')

    def test_get_with_fake_var(self):
        """Test case for config using undefined variable in value
        """
        config.configs = {
            'git_dir': {
                'description': 'Git directory',
                'default': '%work_dir%/git',
                'type': str
            }
        }

        self.assertEqual(Config.get('git_dir'), '%work_dir%/git')

        Config.set('work_dir', 'my-work')

        self.assertEqual(Config.get('git_dir'), 'my-work/git')
        self.assertEqual(Config.get_default('git_dir'), '%work_dir%/git')

    def test_get_with_convertion(self):
        """Test case: Get a value and convert it
        """
        config.configs = {
            'cache_duration': {
                'description': 'Cache duration (in seconds)',
                'default': '10m',  # 10 minutes
                'convert': convert_duration,
                'type': int
            }
        }

        self.assertEqual(Config.get('cache_duration'), 600)

        Config.set('cache_duration', '5m')
        self.assertEqual(Config.get('cache_duration'), 300)

        Config.set('cache_duration', 60)
        self.assertEqual(Config.get('cache_duration'), 60)

    def test_get_with_var_as_default(self):
        """Test case for config using variable as default for other value
        """
        config.configs = {
            'cache_duration': {
                'default': 3600,
                'type': int
            },
            'cache_duration_data1': {
                'default': '%cache_duration%',
                'type': int
            },
            'cache_duration_data2': {
                'default': '%cache_duration%',
                'type': int
            }
        }

        self.assertEqual(Config.get('cache_duration'), 3600)
        self.assertEqual(Config.get('cache_duration_data1'), 3600)
        self.assertEqual(Config.get('cache_duration_data2'), 3600)

        Config.set('cache_duration', 300)

        self.assertEqual(Config.get('cache_duration'), 300)
        self.assertEqual(Config.get('cache_duration_data1'), 300)
        self.assertEqual(Config.get('cache_duration_data2'), 300)


if __name__ == '__main__':
    import unittest
    unittest.main()
