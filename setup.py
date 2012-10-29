"""
Flask-AssetsLite
----------------

A lightweight and simple web assets implementation for Flask.
"""
from setuptools import setup

setup(
    name='Flask-AssetsLite',
    version='0.9',
    license='BSD',
    author='Daniel Simmons',
    author_email='daniel.simmons@tobias.tv',
    description='Simple web assets implementation for Flask',
    long_description=__doc__,
    packages=['flask_assetslite'],
    zip_safe=False,
    install_requires=[
        'Flask'
    ],
    classifiers=[
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ]
)
