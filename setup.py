from setuptools import setup


with open('README.rst', mode='r', encoding='utf-8') as f:
    long_description = f.read()

setup(
    author='Oktay Sancak',
    author_email='oktay.sancak@taggle.com.au',
    classifiers=[
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],
    description='Client library for Taggle''s Corella module',
    include_package_data=True,
    install_requires=['pyserial>=3.4'],
    keywords='taggle corella_lib iot lpwan serial x-bee',
    license='Apache License Version 2.0',
    long_description=long_description,
    name='corella_lib',
    packages=['corella_lib'],
    package_data={'': ['HISTORY.rst', 'LICENSE.txt', 'README.rst']},
    python_requires='>=3.5',
    url='http://corella.taggle.com.au',
    version='0.1.2',
)
