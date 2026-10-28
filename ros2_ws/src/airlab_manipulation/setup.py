from glob import glob

from setuptools import setup

package_name = 'airlab_manipulation'

setup(
    name=package_name,
    version='0.1.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/launch', glob('launch/*.launch.py')),
        ('share/' + package_name + '/config', glob('config/*')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='sejin',
    maintainer_email='sejiny3@gmail.com',
    description='ArUco perception and mobile pick-and-place skills for AIRLAB.',
    license='Apache-2.0',
    entry_points={
        'console_scripts': [
            'aruco_detector = airlab_manipulation.aruco_detector:main',
            'pick_place_demo = airlab_manipulation.pick_place_demo:main',
            'task_planner = airlab_manipulation.task_planner:main',
            'ask = airlab_manipulation.ask:main',
        ],
    },
)
