from setuptools import setup, find_packages
import sys, os
import time

name = 'sillyfacter'
setup(name=name,
      version=open("bin/{}".format(name)).read().split('COLLECTOR_VERSION')[1].split('\'')[1],
      description="""\
Sillyfacter prints JSON facts related to the state of the system. The state here means process running on the host, their open connections and files. Also users logged in, mount points on the host etcetra. These information is useful in mapping out dependencies.""",
      long_description=open('README.txt').read(),
      classifiers=[], # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
      keywords='facter json process lsof mounts facts host os state',
      author='Gautam R Singh',
      author_email='g@ut.am',
      url='https://github.com/hihellobolke/Sillyfacter',
      license='Apache',
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
      include_package_data=True,
      zip_safe=False,
      scripts=['bin/sillyfacter'],
      install_requires=[
          "psutil >= 1.2.1",
          "netifaces >= 0.8",
          "netaddr >= 0.7.10",
          "pymongo",
          # -*- Extra requirements: -*-
      ],
      entry_points="""
      # -*- Entry points: -*-
      """,
      )
