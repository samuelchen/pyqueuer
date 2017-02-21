"""A setuptools based setup module.
See:
https://packaging.python.org/en/latest/distributing.html
https://github.com/pypa/sampleproject
"""

from setuptools import setup, find_packages

PACKAGE = "pyqueuer"
NAME = "PyQueuer"
DESCRIPTION = "A tool for automatically sending/receiving message to/from MQ such as RabbitMQ, Kafka and so on."
AUTHOR = "Samuel Chen"
AUTHOR_EMAIL = "me@samuelchen.net"
URL = "https://github.com/samuelchen/pyqueuer"
VERSION = __import__(PACKAGE).__version__
REQUIREMENTS = []
with open('requirements.txt', 'rt') as f:
    for line in f.readlines():
        REQUIREMENTS.append(line)
with open('README.md', 'rt') as f:
    LONG_DESC = f.read()


setup(
    name=NAME,
    version=VERSION,
    description=DESCRIPTION,
    long_description=LONG_DESC,
    author=AUTHOR,
    author_email=AUTHOR_EMAIL,
    license="GPL 3.0",
    url=URL,

    package_dir={'': '.'},
    packages=find_packages(exclude=["tests.*", "tests"]),
    package_data={
        '': ['*.md', '*.txt', '*.py', '*.ini'],
    },
    # package_data=find_package_data(
    #     PACKAGE,
    #     only_in_packages=False
    # ),
    include_package_data=True,
    platforms='any',

    # What does your project relate to?
    keywords='python mq broker rabbitmq kafka test tool',

    # Must check with "requirements.txt" while releasing.
    # See;
    # https://python-packaging-user-guide.readthedocs.org/en/latest/requirements/#install-requires-vs-requirements-files
    install_requires=REQUIREMENTS,

    classifiers=[
        # How mature is this project? Common values are
        # 2 - Pre-Alpha
        # 3 - Alpha
        # 4 - Beta
        # 5 - Production/Stable
        'Development Status :: 3 - Alpha',

        # Indicate who your project is intended for.
        'Intended Audience :: Developers',
        'Intended Audience :: Education',
        'Intended Audience :: Information Technology',
        'Intended Audience :: System Administrators',

        'Topic :: Internet :: WWW/HTTP :: WSGI',
        'Topic :: Software Development :: Testing',

        # Specify the Python versions you support here. In particular, ensure
        # that you indicate whether you support Python 2, Python 3 or both.
        # 'Programming Language :: Python :: 2.6',
        # 'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',

        "Environment :: Web Environment",
        "License :: OSI Approved :: GPL3 License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Framework :: Django",
    ],
    zip_safe=False,

    # To provide executable scripts, use entry points in preference to the
    # "scripts" keyword. Entry points provide cross-platform support and allow
    # pip to create the appropriate form of executable for the target platform.
    entry_points={
        'console_scripts': [
            'handler = pyqueuer.py',
        ],
    }
)

