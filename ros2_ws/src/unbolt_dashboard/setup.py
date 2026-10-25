from glob import glob

from setuptools import setup

package_name = 'unbolt_dashboard'

setup(
    name=package_name,
    version='0.1.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/launch', glob('launch/*.launch.py')),
        ('share/' + package_name + '/web', glob('web/*')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='sejin',
    maintainer_email='sejiny3@gmail.com',
    description='Web dashboard for UNBOLT over rosbridge.',
    license='Apache-2.0',
    entry_points={
        'console_scripts': [
            'dashboard_server = unbolt_dashboard.dashboard_server:main',
            'dashboard_launcher = unbolt_dashboard.launcher:main',
        ],
    },
)
