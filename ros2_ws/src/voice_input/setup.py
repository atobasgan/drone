from setuptools import find_packages, setup

package_name = 'voice_input'

setup(
    name=package_name,
    version='0.1.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools', 'numpy'],
    zip_safe=True,
    maintainer='atobasgan',
    maintainer_email='atobasgan33@gmail.com',
    description='Ses girisi: mikrofon / WAV -> Silero VAD -> faster-whisper -> /voice/stt.',
    license='MIT',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'stt_node = voice_input.stt_node:main',
            'kayit_al = voice_input.kayit_al:main',
            'stt_karsilastir = voice_input.stt_karsilastir:main',
            'ses_testi = voice_input.ses_testi:main',
            'sentetik_set = voice_input.sentetik_set:main',
        ],
    },
)
