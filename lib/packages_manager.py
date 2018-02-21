# -*- coding: utf-8 -*-

import os
import logging

from pkg_resources import parse_version
from multiprocessing import Pool

from .config import Config
from .cache import Cache
from .tools import Tools
from .makefile_parser.makefile_parser import MakefileParser
from .package_search_update import PackageSearchUpdate
from .package_builder import PackageBuilder

_LOGGER = logging.getLogger(__name__)


class PackagesManager(object):

    def __init__(self, packages_requested):
        self._packages_requested = packages_requested
        self._packages = {}
        self._packages_spk = {}

        self._cache = Cache(duration=Config.get("cache_duration_packages_manager"))

        self.generate_packages_list()
        self.generate_packages_spk_list()

        if not self._packages_requested:
            self._packages_requested = list(self._packages.keys())

        self._packages_requested.sort()

    def _find_packages(self, path):
        """ Find all packages in a directory and return package name
        """
        result = []
        dirname = os.path.basename(path)
        for filename in os.listdir(path):
            makefile = os.path.join(path, filename, 'Makefile')
            if os.path.exists(makefile):
                result.append(dirname + os.path.sep + filename)

        return result

    def get_makefile_path(self, package):
        """ Return Makefile path of a package
        """
        return os.path.join(Config.get('spksrc_git_dir'), package, 'Makefile')

    def generate_package_informations(self, packages, package):
        if not package in packages:
            makefile_path = self.get_makefile_path(package)

            if not os.path.exists(makefile_path):
                _LOGGER.warning("Package %s doesn't exist !", package)
                return

            parser = MakefileParser()
            search_update = PackageSearchUpdate(package, makefile_path)
            search_update.set_parser(parser)

            informations = search_update.get_informations()
            packages[package] = {
                'makefile_path': makefile_path,
                'parser': parser,
                'search_update': search_update,
                'informations': informations,
                'parents': []
            }

            for dep in informations['all_depends']:
                self.generate_package_informations(packages, dep)
                if dep in self._packages and dep not in self._packages[dep]['parents']:
                    self._packages[dep]['parents'].append(package)
                if dep in self._packages_spk and dep not in self._packages_spk[dep]['parents']:
                    self._packages_spk[dep]['parents'].append(package)

    def generate_packages_list(self):
        """ XXX
        """
        cache_filename = 'packages.pkl'
        self._packages = self._cache.load(cache_filename)

        if not self._packages:
            packages = self._find_packages(Config.get('spksrc_git_dir') + 'cross') + self._find_packages(Config.get('spksrc_git_dir') + 'native')

            self._packages = {}
            for package in packages:
                self.generate_package_informations(self._packages, package)

            self._cache.save(cache_filename, self._packages)


    def generate_packages_spk_list(self):
        """ XXX
        """
        cache_filename = 'packages_spk.pkl'
        self._packages_spk = self._cache.load(cache_filename)

        if not self._packages_spk:
            packages = self._find_packages(Config.get('spksrc_git_dir') + 'spk')

            self._packages_spk = {}
            for package in packages:
                self.generate_package_informations(self._packages_spk, package)

            self._cache.save(cache_filename, self._packages_spk)

    def package_search_update(self, package):

        search_update = self._packages[package]['search_update']

        search_update.search_updates()

        return [package, search_update.get_informations()]

    def check_update_packages(self):
        """ Print all dependencies
        """
        pool = Pool(processes=Config.get('nb_jobs'))

        packages = pool.map(self.package_search_update, self._packages_requested)

        for package in packages:
            self._packages[package[0]]['informations'] = package[1]

        cache_filename = 'packages.pkl'
        self._cache.save(cache_filename, self._packages)

    def check_version_isvalid(self, current, new):
        if not Config.get('build_prerelease_allowed') and new['is_prerelease']:
            return False

        current_p = parse_version(current)
        new_p = parse_version(new['version'])
        if Config.get('build_major_release_allowed'):
            return new_p > current_p

        major_version = Tools.get_next_major_version(current_p)
        if major_version and new_p >= major_version:
            return False

        return new_p > current_p

    def get_next_version(self, package):
        """ Get the next version to update using the parameters (allow_major_release, ...) """

        if package not in self._packages:
            return None

        if not self._packages[package]['informations']['versions']:
            return None

        current_version = self._packages[package]['informations']['version']

        result = {'version': current_version}
        if self._packages[package]['informations']['method'] == 'common':
            for _, new in self._packages[package]['informations']['versions'].items():
                if self.check_version_isvalid(current_version, new):
                    result = new

        else:
            result = {'version': next(iter(self._packages[package]['informations']['versions'])) }

        return result



    def get_package(self, package):
        """ Return package informations
        """
        return self._packages[package]



    def pprint_next_version(self):
        """ Print the next version to update using the parameters (allow_major_release, ...)
        """
        print("{:<30} {:<10} {:<30} {:<30}".format("Package", "New ?", "Current version", "Next version"))
        for package in self._packages_requested:
            next_version = self.get_next_version(package)
            new_version_state = "NO"
            new_version = ""
            if next_version:
                new_version = next_version['version']
                if self._packages[package]['informations']['version'] != new_version:
                    new_version_state = "YES"

            print("{:<30} {:<10} {:<30} {:<30}".format(package, new_version_state, self._packages[package]['informations']['version'], new_version))

    def pprint_new_versions(self):
        """ Print new versions on packages
        """
        for package in self._packages_requested:
            print("{} ({}):".format(package, self._packages[package]['informations']['version']))
            for (version, _) in self._packages[package]['informations']['versions'].items():
                print(" - {}".format(version))

    def pprint_deps(self, package, depth=0):
        """ Print all dependencies
        """
        print('  ' * depth + " - " + package)
        depends = []
        if package in self._packages:
            depends += self._packages[package]['informations']['all_depends']
        if package in  self._packages_spk:
            depends += self._packages_spk[package]['informations']['all_depends']

        for deps in set(depends):
            self.pprint_deps(deps, depth + 1)

    def pprint_parent_deps(self, package, depth=0):
        """ Print all parent dependencies
        """
        print('  ' * depth + " - " + package)
        parents = []
        if package in self._packages:
            parents += self._packages[package]['parents']
        if package in  self._packages_spk:
            parents += self._packages_spk[package]['parents']
        for deps in set(parents):
            self.pprint_parent_deps(deps, depth + 1)

        # packages = self.check_update_packages()

        # builder = PackageBuilder(packages, update_deps=Config.get('update_deps'),
        #                          allow_major_release=Config.get('allow_major_release'), allow_prerelease=Config.get('allow_prerelease'))
        # builder.set_spksrc_dir(os.path.join(
        #     Config.get('work_dir'), PackageBuilder.default_spksrc_dir))
        # if Config.get('verbose'):
        #     builder.set_verbose(True)

        # builder.build()
        # pprint.pprint(packages)