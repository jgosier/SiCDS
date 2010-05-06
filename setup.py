from setuptools import setup, find_packages

version = '0.0.1dev'
url = 'http://github.com/appfrica/SiCDS'

try:
    import os
    doc_dir = os.path.join(os.path.dirname(__file__), 'docs')
    readme = open(os.path.join(doc_dir, 'README.rst'))
    long_description = readme.read()
except IOError:
    long_description = 'Please see {0} for more info'.format(url)

setup(name='SiCDS',
      version=version,
      description='SwiftRiver Content Duplication Service',
      long_description=long_description,
      install_requires=[
          'Python>=2.6.5',
          'PyYAML',
          'WebOb',
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
