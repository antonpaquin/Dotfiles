from distutils.core import setup

setup(
    name='configurator',
    version='1.0.0',
    description='Keep track of config files',
    author='Anton Paquin',
    author_email='python@antonpaqu.in',
    packages=['configurator'],
    entry_points={
        'console_scripts': [
            'configurator = configurator:main'
        ],
    },
)
