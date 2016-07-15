from setuptools import setup, Extension

DISTNAME = 'django-tethne-client'
AUTHOR = 'E. Peirson, Digital Innovation Group @ ASU'
MAINTAINER = 'Erick Peirson'
MAINTAINER_EMAIL = 'erick [dot] peirson [at] asu [dot] edu'
DESCRIPTION = ('Python client for django-tethne JSON API.')
LICENSE = 'GNU GPL 3'
URL = 'http://diging.github.io/tethne/'
VERSION = '0.1.2'

PACKAGES = ['tethneweb']

setup(
    name=DISTNAME,
    author=AUTHOR,
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
    ],
)
