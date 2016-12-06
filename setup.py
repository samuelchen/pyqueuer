"""A setuptools based setup module.
See:
https://packaging.python.org/en/latest/distributing.html
https://github.com/pypa/sampleproject
"""

from setuptools import setup, find_packages

setup(
    # PyQueuer
    name='pyqueuer',

    # Version is under discussion.
    version='1.0.0',

    description='A tool for automatically sending/receiving message to/from MQ.',

    # The project's main homepage
    url='https://github.com/samuelchen/pyqueuer',
    author='Samuel Chen',
    author_email='me@samuelchen.net',

    # Need to further confirm with legal team.
    license='GPL 3.0',

    # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        # How mature is this project? Common values are
        # 2 - Pre-Alpha
        # 3 - Alpha
        # 4 - Beta
        #   5 - Production/Stable
        'Development Status :: 3 - Alpha',

        'Environment :: No Input/Output (Daemon)',

        # Indicate who your project is intended for.
        'Intended Audience :: Developer, Tester',
        'Topic :: Internet :: WWW/HTTP :: WSGI',

        # Specify the Python versions you support here. In particular, ensure
        # that you indicate whether you support Python 2, Python 3 or both.
        # 'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        # 'Programming Language :: Python :: 3',
        # 'Programming Language :: Python :: 3.2',
        # 'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        # 'Programming Language :: Python :: 3.5',
    ],

    # What does your project relate to?
    keywords='python mq rabbitmq test ',

    # Must check with "requirements.txt" while releasing.
    # See;
    # https://python-packaging-user-guide.readthedocs.org/en/latest/requirements/#install-requires-vs-requirements-files
    install_requires=[],

    packages=find_packages(exclude=['docs', 'tests']),
    include_package_data=True,
    platforms='any',

    # To provide executable scripts, use entry points in preference to the
    # "scripts" keyword. Entry points provide cross-platform support and allow
    # pip to create the appropriate form of executable for the target platform.
    entry_points={
        'console_scripts': [
            'handler = pyqueuer:manage',
        ],
    }
)
