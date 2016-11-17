from setuptools import setup, Extension

DISTNAME = 'django-tethne-client'
AUTHOR = 'E. Peirson, Digital Innovation Group @ ASU'
AUTHOR_EMAIL = 'erick.peirson@asu.edu'
MAINTAINER = 'Erick Peirson'
MAINTAINER_EMAIL = 'erick.peirson@asu.edu'
DESCRIPTION = ('Python client for django-tethne JSON API.')
LICENSE = 'GNU GPL 3'
URL = 'http://diging.github.io/tethne/'
VERSION = '0.2.7'

PACKAGES = ['tethneweb']

setup(
    name=DISTNAME,
    author=AUTHOR,
    author_email=AUTHOR_EMAIL,
    maintainer=MAINTAINER,
    maintainer_email=MAINTAINER_EMAIL,
    description=DESCRIPTION,
    license=LICENSE,
    url=URL,
    version=VERSION,
    packages = PACKAGES,
    include_package_data=True,
    install_requires=[
        'requests==2.10',
        'jsonpickle==0.9.3'
    ],
)
