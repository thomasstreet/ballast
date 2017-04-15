#!/usr/bin/env python

import re
import os
from setuptools import setup, find_packages, Command


def get_version():

    # create a dummy file if it doesn't exist
    if not os.path.exists('version.py'):
        with open('version.py', 'w') as f:
            f.write("__version__ = '0.0.0'\n")

    # now open and parse the version number
    with open('version.py') as f:
        contents = f.read()
        version = re.search(r"__version__\s*=\s*'(.*)'", contents, re.M).group(1)
        return version


class GenerateVersionCommand(Command):
    """
    Create a `version.py` file containing the
    specified version information.
    """
    description = 'generate version number file'

    user_options = [
        ('sha', None, 'include commit SHA hash'),
    ]

    def initialize_options(self):
        self.sha = False

    def finalize_options(self):
        self.sha = True if int(self.sha) == 1 else False

    def run(self):

        major, minor, revision, offset, sha = self._get_version_from_git()

        print("Major: %s" % major)
        print("Minor: %s" % minor)
        print("Revision: %s" % revision)
        print("Offset: %s" % offset)
        print("Sha: %s" % sha)

        with open('version.py', 'w') as f:
            if self.sha:
                f.write("__version__ = '%s.%s.%s-%s'\n" % (major, minor, offset, sha))
            else:
                f.write("__version__ = '%s.%s.%s'\n" % (major, minor, offset))

    @staticmethod
    def _get_version_from_git():
        import re
        import git

        # parse our version number
        # from a combination of the
        # git revision count as well
        # as git tagged  version
        repo = git.Repo()
        head = repo.head.commit
        revision = head.count()
        d = repo.git.describe(long=True, tags=True)
        m = re.search('^v([0-9]*)\.([0-9]*)\.[0-9]*-([0-9]*)-(.*)$', d)

        assert m is not None

        g = m.groups()

        return g[0], g[1], revision, g[2], g[3]


with open('README.rst', 'r') as f:
    readme = f.read()


setup(name='balast',
      version=get_version(),
      description='Balast client-side load-balancing framework',
      long_description=readme,
      author='Justin Smith',
      author_email='smith.justin.c@gmail.com',
      maintainer='Justin Smith',
      maintainer_email='smith.justin.c@gmail.com',
      license='MIT',
      url='https://github.com/radishllc/balast',
      packages=find_packages(exclude=['test', 'docs']),
      package_data={
          'balast': ['../version.py', '../LICENSE'],
      },
      include_package_data=True,
      setup_requires=['pytest-runner'],
      tests_require=['pytest', 'mock'],
      install_requires=['requests', 'gevent'],
      extras_require={
          'dns': ['dnspython>=1.15.0']
      },
      cmdclass={
          'version': GenerateVersionCommand
      },
      classifiers=[
          # How mature is this project? Common values are
          #   3 - Alpha
          #   4 - Beta
          #   5 - Production/Stable
          # "Development Status :: 1 - Planning",
          # "Development Status :: 2 - Pre-Alpha",
          "Development Status :: 3 - Alpha",
          # "Development Status :: 4 - Beta",

          # Indicate who your project is intended for
          'Intended Audience :: Developers',
          'Topic :: Software Development :: Libraries :: Python Modules',

          # Pick your license as you wish (should match "license" above)
          'License :: OSI Approved :: MIT License',

          # Specify the Python versions you support here. In particular, ensure
          # that you indicate whether you support Python 2, Python 3 or both.
          # 'Programming Language :: Python :: 2',
          # 'Programming Language :: Python :: 2.6',
          'Programming Language :: Python :: 2.7',
          # 'Programming Language :: Python :: 3',
          # 'Programming Language :: Python :: 3.2',
          # 'Programming Language :: Python :: 3.3',
          # 'Programming Language :: Python :: 3.4',
      ],
      keywords='alpha development load-balancing',
      )
