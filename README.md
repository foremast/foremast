# Spinnaker Pipes

This repository will contain scripts for all of the "pipes" tasks for Spinnaker
deployments.


## Basic Task Overview

1. Create logical Spinnaker app
1. Create/modify ELB
1. Create/modify server group/ASG
1. Create/modify Security Groups
1. Create/modify application pipeline

These are designed to be loosely coupled applications and we will continue to
update this README as the project grows.


## Technology Used

1. Python3
1. Jinja2 templating
1. Python Requests
1. Argparse for arguements
1. Boto3 (direct AWS access to parts not exposed by Spinnaker, e.g. S3)
