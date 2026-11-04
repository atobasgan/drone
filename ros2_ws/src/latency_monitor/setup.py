from setuptools import find_packages, setup

package_name = 'latency_monitor'

setup(
    name=package_name,
    version='0.1.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='atobasgan',
    maintainer_email='atobasgan33@gmail.com',
    description='Asama asama gecikme olcumu (t0..t5) ve ozet tablosu.',
    license='MIT',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'monitor_node = latency_monitor.monitor_node:main',
            'ozet = latency_monitor.ozet:main',
        ],
    },
)
