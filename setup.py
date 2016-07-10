# coding: utf-8
from setuptools import setup, find_packages
from pip.req import parse_requirements

install_requires = [str(ir.req) for ir in parse_requirements("requirements.txt", session=False)]


setup(
    name='hirosql',
    version='0.2',
    author='Hiroyuki Ishii',
    author_email="hiroyuki.ishii.42@gmail.com",
    # url="http://",
    py_modules=['hirosql'],
    packages=find_packages(),
    description='A small development tool for mysql or other databases',
    dependency_links=[],
    keywords=['sql'],
    install_requires=install_requires,
    entry_points='''
        [console_scripts]
        hirosql=hirosql.main:cli
    ''',
)
