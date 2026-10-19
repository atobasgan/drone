from setuptools import find_packages, setup

package_name = 'mission_executor'

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
    description='Guvenlik katmani + durum makinesi + PX4 offboard kontrol.',
    license='MIT',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'executor_node = mission_executor.executor_node:main',
            'konum_izleyici = mission_executor.konum_izleyici:main',
        ],
    },
)
