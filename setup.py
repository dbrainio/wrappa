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
        command.append(os.getcwd() + '/wrappa')
        self.announce(
            'Running command: %s' % str(command),
            level=distutils.log.INFO)
        try:
            subprocess.check_call(command)
        except:
            pass


install_requires = [
    'aiohttp>=3.4.4'
    'python-consul>=1.0.1',
    'requests>=2.13.0',
    'requests-toolbelt>=0.8.0',
    'pyyaml>=3.13',
    'numpy>=1.14.0',
    'Pillow>=5.0.0'
]

CONFIG = {
    'name': 'wrappa',
    'url': '',
    'version': '0.4.0',
    'description': 'wrappa wraps ds app in http server',
    'author': 'seka17',
    'test_suite': 'wrappa',
    'packages': find_packages(exclude=['dummy', 'tests', '*.tests', '*.tests.*']),
    'entry_points': {
        'console_scripts': [
            'wrappa = wrappa.__main__:main',
            'wrappa-validate = wrappa.validate:main'
        ],
    },
    'install_requires': install_requires,
    'cmdclass': {
        'pylint': PylintCommand
    },
}

setup(**CONFIG)
