# Copyright (C) 2010 Ushahidi Inc. <jon@ushahidi.com>,
# Joshua Bronson <jabronson@gmail.com>, and contributors
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 3
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the
# Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor,
# Boston, MA  02110-1301
# USA

from os.path import dirname, join
from sys import exit, stderr, version_info

def die(msg):
    stderr.write(msg+'\n')
    exit(1)

if not ((2, 6, 5) <= version_info < (3,)):
    die('Python>=2.6.5,<3 required.') 

try:
    from setuptools import setup, find_packages
except ImportError:
    die('Could not import setuptools. Install distribute? '
        'http://packages.python.org/distribute/')

version = '0.0.1dev'
url = 'http://github.com/appfrica/SiCDS'
desc_filename = 'README.rst'
desc_path = join(dirname(__file__), desc_filename)
try:
    desc_file = open(desc_path)
except IOError:
    long_description = 'Please see {0} for more info'.format(url)
else:
    long_description = desc_file.read()
    desc_file.close()

setup(name='SiCDS',
      version=version,
      description='SwiftRiver Content Duplication Service',
      long_description=long_description,
      install_requires=[
          #'Python>=2.6.5,<3.0'
          'WebOb==0.9.8',
          'simplejson==2.1.1',
          ],
      extras_require = {
          'CouchDB': ["CouchDB==0.7"],
          'MongoDB': ["pymongo==1.6"],
          'Tornado': ["Tornado==0.2"],
          'tests': ["WebTest==1.2.1"],
          },
      entry_points=dict(
          console_scripts=[
              'sicdsapp = sicds.app:main',
              'sicdsshell = sicds.shell:main',
              ]
          ),
      classifiers=[
          'Development Status :: 3 - Alpha',
          'License :: OSI Approved :: GNU General Public License (GPL)',
          ],
      keywords='ushahidi swiftriver sicds',
      author='Joshua Bronson',
      author_email='jabronson@gmail.com',
      url=url,
      license='GPL',
      packages=find_packages(exclude=['tests']),
      include_package_data=True,
      zip_safe=True,
      )
