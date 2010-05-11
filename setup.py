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
desc_dir = 'docs'
desc_filename = 'README.rst'
desc_path = join(join(dirname(__file__), desc_dir), desc_filename)
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
          },
      entry_points=dict(
          console_scripts=[
              'sicdsapp = sicds.app:main'
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
