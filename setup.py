from setuptools import setup

INSTALL_REQUIRES = list()
with open('requirements.txt') as requirements_file:
    for requirement in requirements_file:
        INSTALL_REQUIRES.append(requirement)
INSTALL_REQUIRES = list(set(INSTALL_REQUIRES))

exec(open('foreigneffigy/version.py').read())

setup(
    name='foreigneffigy',
    packages=['foreigneffigy'],
    version=__version__,
    install_requires=INSTALL_REQUIRES
)
