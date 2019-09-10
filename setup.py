#!/usr/bin/env python3
#   Foremast - Pipeline Tooling
#
#   Copyright 2018 Gogo, LLC
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
"""Foremast installer"""

from setuptools import find_packages, setup

with open('requirements.txt', 'rt') as reqs_file:
    REQUIREMENTS = reqs_file.readlines()

setup(
    name='foremast',
    description='Tools for creating infrastructure and Spinnaker Pipelines.',
    long_description=open('README.rst').read(),
    author='Gogo DevOps',
    author_email='ps-devops-tooling@example.com',
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    setup_requires=['setuptools_scm'],
    use_scm_version={'local_scheme': 'dirty-tag'},
    install_requires=REQUIREMENTS,
    include_package_data=True,
    keywords="aws gogo infrastructure netflixoss python spinnaker",
    url='https://github.com/foremast/foremast',
    download_url='https://github.com/foremast/foremast',
    platforms=['OS Independent'],
    license='Apache License (2.0)',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
    ],
    entry_points={
        'console_scripts': [
            'create-app=foremast.app.__main__:main',
            'create-configs=foremast.configs.__main__:main',
            'create-dns=foremast.dns.__main__:main',
            'create-elb=foremast.elb.__main__:main',
            'create-iam=foremast.iam.__main__:main',
            'create-pipeline=foremast.pipeline.__main__:main',
            'create-s3=foremast.s3.__main__:main',
            'create-sg=foremast.securitygroup.__main__:main',
            'destroy-dns=foremast.dns.destroy_dns.__main__:main',
            'destroy-elb=foremast.elb.destroy_elb.__main__:main',
            'destroy-iam=foremast.iam.destroy_iam.__main__:main',
            'destroy-s3=foremast.s3.destroy_s3.__main__:main',
            'destroy-sg=foremast.securitygroup.destroy_sg.__main__:main',
            'full-destroy=foremast.destroyer:main',
            'prepare-app-pipeline=foremast.runner:prepare_app_pipeline',
            'foremast-pipeline=foremast.runner:prepare_app_pipeline',
            'prepare-infrastructure=foremast.runner:prepare_infrastructure',
            'foremast-infrastructure=foremast.runner:prepare_infrastructure',
            'prepare-onetime-pipeline=foremast.runner:prepare_onetime_pipeline',
            'foremast-pipeline-onetime=foremast.runner:prepare_onetime_pipeline',
            'create-scaling-policy=foremast.runner:create_scaling_policy',
            'foremast-scaling-policy=foremast.runner:create_scaling_policy',
            'foremast-scheduled-actions=foremast.runner:create_scheduled_actions',
            'rebuild_pipelines=foremast.runner:rebuild_pipelines',
            'foremast-pipeline-rebuild=foremast.runner:rebuild_pipelines',
            'foremast-deploy-s3app=foremast.runner:deploy_s3app',
            'foremast-promote-s3app=foremast.runner:promote_s3app',
            'slack-notify=foremast.slacknotify.__main__:main',
            'foremast=foremast.__main__:main',
        ]
    }, )
