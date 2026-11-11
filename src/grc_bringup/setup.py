# SPDX-License-Identifier: Apache-2.0

from setuptools import setup

package_name = 'grc_bringup'

setup(
    name=package_name,
    version='1.0.0',
    packages=[package_name],
    data_files=[],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Arpan Bom',
    maintainer_email='applycoding@gmail.com',
    description='Simulation bringup helpers',
    license='Apache-2.0',
)
