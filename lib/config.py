# -*- coding: utf-8 -*-

import re
import six
import logging
import multiprocessing
from datetime import datetime
import parsedatetime


def convert_duration(value):
    """ Convert an input duration in seconds
    """
    if type(value) is int:
        return value

    cal = parsedatetime.Calendar()
    date_now = datetime.now().replace(microsecond=0)
    date, _ = cal.parseDT(value, sourceTime=date_now)
    return (date - date_now).total_seconds()


configs = {
    'debug_level': {
        'description': 'Debug level: DEBUG, INFO, WARNING, ERROR, CRITICAL',
        'default': 'INFO',
        'type': int,
        'convert': logging.getLevelName
    },

    'nb_jobs': {
        'description': 'Number of jobs',
        'default': multiprocessing.cpu_count(),
        'type': int
    },

    'work_dir': {
        'description': 'Work directory: Contains cache, spksrc source, ...',
        'default': 'work',
        'type': str
    },

    'spksrc_git_dir': {
        'description': 'Root directory of spksrc',
        'default': '%work_dir%/spksrc-git',
        'type': str
    },
    'spksrc_git_uri': {
        'description': 'Spksrc repository',
        'default': 'https://github.com/SynoCommunity/spksrc.git',
        'type': str
    },
    'spksrc_git_branch': {
        'description': 'Default branch to checkout the spksrc repository',
        'default': 'master',
        'type': str
    },

    'cache_enabled': {
        'description': 'Define if cache is enabled',
        'default': True,
        'type': bool
    },
    'cache_dir': {
        'description': 'Cache directory',
        'default': '%work_dir%/cache',
        'type': str
    },
    'cache_duration': {
        'description': 'Global cache duration',
        'default': '7d',
        'type': int,
        'convert': convert_duration
    },
    'cache_duration_packages_manager': {
        'description': 'Cache duration for packages list',
        'default': '%cache_duration%',
        'type': int,
        'convert': convert_duration
    },
    'cache_duration_search_update_download': {
        'description': 'Cache duration for package update: download page content, versions found',
        'default': '%cache_duration%',
        'type': int,
        'convert': convert_duration
    },

    'build_update_deps': {
        'description': 'Update deps before build the current package',
        'default': False,
        'type': bool
    },
    'build_major_release_allowed': {
        'description': 'Allow to update to next major version',
        'default': False,
        'type': bool
    },
    'build_prerelease_allowed': {
        'description': 'Allow prerelease version',
        'default': False,
        'type': bool
    },

    # 'packages': {
    #     'description': 'List of packages in input',
    #     'default': [],
    #     'type': list
    # }
}


class Config:

    configs_cached = {}
    regex_config_replace = re.compile('%\w+%')

    @staticmethod
    def _parse_value(getter, value):
        if isinstance(value, str):
            for match in Config.regex_config_replace.findall(value):
                replace_value = getter(match[1:-1], None)
                if replace_value is not None:
                    if value == match:
                        value = replace_value
                        break
                    else:
                        value = value.replace(match, str(replace_value))
        return value

    @staticmethod
    def get_keys():
        return configs.keys()

    @staticmethod
    def get_default(property_name, default=None):
        """ Get default property value
        """
        prop = configs.get(property_name)
        if not prop:
            return default

        value = prop.get('default')
        value = Config._parse_value(Config.get_default, value)

        if not value and default:
            return default

        return value

    @staticmethod
    def get(property_name, default=None):
        """ Get property value
        """
        if property_name in Config.configs_cached and Config.configs_cached[property_name]:
            return Config.configs_cached[property_name]

        prop = configs.get(property_name)
        if not prop:
            return default

        value = prop.get('value')
        if value is None:
            value = prop.get('default')
        value = Config._parse_value(Config.get, value)

        value = Config.convert(prop, value)
        Config.configs_cached[property_name] = value

        if not value and default:
            return default

        return value

    @staticmethod
    def set(property_name, value):
        """ Set new property value
        """
        if property_name not in configs:
            configs[property_name] = {}
        Config.clear_cache(property_name)
        configs[property_name]['value'] = value
        return True

    @staticmethod
    def clear_cache(property_name):
        """ Clear cache for property
        """
        if property_name in Config.configs_cached:
            del Config.configs_cached[property_name]

        prop_var = '%' + property_name + '%'
        for (key, prop) in six.iteritems(configs):
            if key in Config.configs_cached:
                prop_value = prop.get('value')
                if prop_value is None:
                    prop_value = prop.get('default')
                if isinstance(prop_value, str) and prop_var in prop_value:
                    Config.clear_cache(key)

    @staticmethod
    def convert(prop, value):
        """ Convert value to property type
        """
        if value:
            if 'convert' in prop and callable(prop['convert']):
                value = prop['convert'](value)

            if 'type' in prop:
                type_ = prop['type']
                return type_(value)
        return value
