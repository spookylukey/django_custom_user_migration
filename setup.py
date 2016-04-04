#!/usr/bin/env python
# -*- coding: utf-8 -*-


try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup


with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read().replace('.. :changelog:', '')

requirements = [
    "Django>=1.8",
]

test_requirements = requirements


setup(
    name='django_custom_user_migration',
    version='0.2.0',
    description="django_custom_user_migration will help you create a migration to using "
    "a custom User model with Django",
    long_description=readme + '\n\n' + history,
    author="Luke Plant",
    author_email='L.Plant.98@cantab.net',
    url='https://bitbucket.com/spookylukey/django_custom_user_migration',
    packages=[
        'django_custom_user_migration',
    ],
    package_dir={'django_custom_user_migration':
                 'django_custom_user_migration'},
    include_package_data=True,
    install_requires=requirements,
    license="BSD",
    zip_safe=False,
    keywords='Django custom user model migration',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        "Programming Language :: Python :: 2",
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
    ],
    test_suite='tests',
    tests_require=test_requirements,
)
