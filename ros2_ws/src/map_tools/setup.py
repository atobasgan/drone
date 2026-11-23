from setuptools import find_packages, setup

package_name = 'map_tools'

setup(
    name=package_name,
    version='0.1.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools', 'requests'],
    zip_safe=True,
    maintainer='atobasgan',
    maintainer_email='atobasgan33@gmail.com',
    description='Faz 5: harita komutlari (en yakin yer, isimle arama) - OSM ve Google Places.',
    license='MIT',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'harita_node = map_tools.harita_node:main',
            'places_node = map_tools.places_node:main',
        ],
    },
)
