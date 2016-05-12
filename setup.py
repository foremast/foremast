#!/usr/bin/env python3
from setuptools import find_packages, setup

with open('requirements.txt', 'rt') as reqs_file:
    reqs_list = reqs_file.readlines()

setup(name='foremast',
      version='2.1',
      description='Tools for creating infrastructure and Spinnaker Pipelines.',
      long_description=open('README.md').read(),
      author='Gogo DevOps',
      author_email='ps-devops-tooling@example.com',
      packages=find_packages(where='src'),
      package_dir={'': 'src'},
      install_requires=reqs_list,
      include_package_data=True,
      keywords="aws gogo infrastructure netflixoss python spinnaker",
      url='https://github.com/gogoair/foremast',
      download_url='https://github.com/gogoair/foremast',
      platforms=['OS Independent'],
      license='MIT',
      classifiers=[
          'Development Status :: 5 - Production/Stable',
          'Intended Audience :: Developers',
          'Programming Language :: Python :: 3.4',
          'Programming Language :: Python :: 3.5',
          'License :: OSI Approved :: MIT License',
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
              'destroy-elb=foremast.elb.destroy_elb.__main__:main',
              'destroy-iam=foremast.iam.destroy_iam.__main__:main',
              'destroy-s3=foremast.s3.destroy_s3.__main__:main',
              'destroy-sg=foremast.securitygroup.destroy_sg.__main__:main',
          ]
      }, )
