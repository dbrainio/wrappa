# pylint: skip-file

import distutils.cmd
import distutils.log
import os
import subprocess
import unittest

from setuptools import find_packages, setup


class PylintCommand(distutils.cmd.Command):
    """A custom command to run Pylint on all Python source files."""

    description = 'run Pylint on Python source files'
    user_options = [
        # The format is (long option, short option, description).
        ('pylint-rcfile=', None, 'path to Pylint config file'),
    ]

    def initialize_options(self):
        """Set default values for options."""
        # Each user option must be listed here with their default value.
        self.pylint_rcfile = '.pylintrc'

    def finalize_options(self):
        """Post-process options."""
        if self.pylint_rcfile:
            assert os.path.exists(self.pylint_rcfile), (
                'Pylint config file %s does not exist.' % self.pylint_rcfile)

    def run(self):
        """Run command."""
        command = ['pylint']
        if self.pylint_rcfile:
            command.append('--rcfile=%s' % self.pylint_rcfile)
        command.append(os.getcwd() + '/dbrdsw')
        self.announce(
            'Running command: %s' % str(command),
            level=distutils.log.INFO)
        try:
            subprocess.check_call(command)
        except:
            pass


install_requires = [
    'Flask-RESTful>=0.3.6',
    'Flask>=1.0.2',
    'python-consul>=1.0.1'
]

CONFIG = {
    'name': 'dbrdsw',
    'url': '',
    'version': '0.0.2',
    'description': 'dbrdsw wraps ds app in http server',
    'author': 'skananykhin',
    'test_suite': 'dbrdsw',
    'packages': find_packages(exclude=['dummy', 'tests', '*.tests', '*.tests.*']),
    'entry_points': {
        'console_scripts': [
            'dbrdsw = dbrdsw.__main__:main',
        ],
    },
    'install_requires': install_requires,
    'cmdclass': {
        'pylint': PylintCommand
    },
}

setup(**CONFIG)
