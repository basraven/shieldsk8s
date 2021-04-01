from os import path
from setuptools import setup

here = path.abspath(path.dirname(__file__))

setup(
    name='shieldsk8s',
    use_scm_version=True,
    py_modules=['shieldsk8s'],
    author='Sebastiaan Raven',
    url='https://github.com/basraven/shieldsk8s',
    description='Integrate shields.io with Kubernetes state backend',
    setup_requires=['setuptools_scm'],
    install_requires=[
        'click>=7,<8',
        'kubernetes>=8,<9',
        'requests>=2,<3',
        'flask>=1.1,<2',
        'requests>=2,<3'
    ],
    entry_points={
        'console_scripts': [
            'shieldsk8s = shieldsk8s:cli'
        ]
    },
    package_data={'': ['LICENSE', 'README.md']}
)
