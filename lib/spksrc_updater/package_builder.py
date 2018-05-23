# -*- coding: utf-8 -*-

import logging
import pprint
from pkg_resources import parse_version

import git as git

from spksrc_updater.config import Config
from spksrc_updater.tools import Tools

_LOGGER = logging.getLogger(__name__)


class PackageBuilder(object):

    def __init__(self, package):
        self._verbose = False
        self._package = package
        self._spksrc_dir = Config.get('spksrc_git_dir')
        self._packages_build = []

    def set_spksrc_dir(self, spksrc_dir):
        """ Set spksrc directory
        """
        self._spksrc_dir = spksrc_dir

    def prepare_spskrc_dir(self):
        """ Prepare the spksrc directory to build
        """

        # Clone repo if not exists
        if not os.path.exists(self._spksrc_dir):
            _LOGGER.info("Clone repository: %s", Config.get('spksrc_git_uri'))
            try:
                git.Repo.clone_from(
                    Config.get('spksrc_git_uri'), self._spksrc_dir)
            except git.GitCommandError as exception:
                _LOGGER.info("Error to clone git")
                return

        # Fetch and pull
        _LOGGER.info("Fetch and pull git")
        repo = git.Repo(self._spksrc_dir)

        # Fetch and pull all remotes
        for remote in repo.remotes:
            remote.fetch()
            remote.pull()

        # Reset hard
        _LOGGER.info("Reset hard")
        repo.head.reset(index=True, working_tree=True)

        # Checkout master
        _LOGGER.info("Checkout master")
        repo.refs.master.checkout()

    def build(self):
        # Prepare spksrc directory by cloning the repository, reset hard and checkout master
        self.prepare_spskrc_dir()

        # Loop on packages to the tree of dependances
        # self.create_deps_tree()

        #

        """
        if 'cross/x265' in self._packages:
            pprint.pprint(self._packages['cross/x265'])
        else:
            pprint.pprint(self._packages)
        """

        for package in self._packages:
            if self._packages[package]['version']:
                _LOGGER.info("%s %s", package, self._packages[package]['version'])
            else:
                _LOGGER.info(package)
            pprint.pprint(self._packages[package])
            #version = self.get_new_version(package)
            # if version:
            #    pprint.pprint(version)
