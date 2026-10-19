from glob import glob

from setuptools import find_packages, setup

package_name = 'command_parser'

setup(
    name=package_name,
    version='0.1.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/data', glob('data/*.jsonl')),
    ],
    install_requires=['setuptools', 'requests'],
    zip_safe=True,
    maintainer='atobasgan',
    maintainer_email='atobasgan33@gmail.com',
    description='Turkce metin -> drone komutu (normalizasyon, hizli yol, LLM).',
    license='MIT',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'parser_node = command_parser.parser_node:main',
            'degerlendir = command_parser.degerlendir:main',
        ],
    },
)
