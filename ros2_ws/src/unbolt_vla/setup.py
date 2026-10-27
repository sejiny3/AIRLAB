from setuptools import setup

package_name = 'unbolt_vla'

setup(
    name=package_name,
    version='0.1.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='sejin',
    maintainer_email='sejiny3@gmail.com',
    description='A small vision-language-action policy for the UNBOLT pick: demos, training, evaluation, ROS node.',
    license='Apache-2.0',
    entry_points={
        'console_scripts': [
            'record = unbolt_vla.record:main',
            'train = unbolt_vla.train:main',
            'evaluate = unbolt_vla.evaluate:main',
            'vla_pick = unbolt_vla.vla_pick_node:main',
        ],
    },
)
