# Spinnaker Pipes

This repository will contain scripts for all of the "pipes" tasks for Spinnaker
deployments.

## Basic Task Overview

These are designed to be loosely coupled applications and we will continue to
update this README as the project grows.

## Usage

```bash
cd ./pipes/
python pipes/app/create_app.py -h
python -m pipes.configs -h
python pipes/dns/create_dns.py -h
python pipes/elb/create_elb.py -h
python -m pipes.iam -h
python pipes/pipeline/create_pipeline.py -h
python -m pipes.s3 -h
python pipes/securitygroup/create_securitygroup.py -h
```

### Testing

```bash
virtualenv venv
source ./venv/bin/activate
pip install -U -r requirements-dev.txt
./runtests.py
```

## Implementation

See `pipes-pipeline-prepare` in [dsl.groovy](runway/dsl.groovy) for Jenkins Job
configuration.

1. Create logical Spinnaker app (triggered by Git Hook)
1. Call downstream Job to manage infrastructure
1. Read configurations from `application-master-{env}.json` and `pipeline.json`
1. Create/modify IAM Profile and Role
1. Create/skip S3 Archaius application.properties file
1. Create/modify Security Groups
1. Create/modify ELB
1. Create DNS record to ELB
1. Create/modify application pipeline

### Not Used

1. Create/modify server group/ASG

    * Part of the Pipeline creation

## Technology Used

See [requirements](requirements.txt) for package listing.

1. Python3
1. Jinja2 templating
1. Python Requests
1. Argparse for arguments
1. Boto3 (direct AWS access to parts not exposed by Spinnaker, e.g. S3)

## Runway Updates

To begin using the Spinnaker deployment system, a few changes will be needed to
the `runway` directory to trigger the tooling.

### runway/dsl.groovy

Remove any downstream Jobs as Spinnaker will poll for the main Job for
completion.

```groovy
job("$SRC_JOB") {
    publishers {
        archiveArtifacts('runway/FS_ROOT/etc/gogo/jenkins_vars, RPMS/x86_64/*.rpm')
        downstreamParameterized {
            // Delete
        }
    }
}
```

### runway/pipeline.json

A new file, `pipeline.json`, will be needed in the `runway` directory to trigger
the creation of the Spinnaker Application and Pipelines for each deployment
environment.

#### Minimum

```json
{
    "deployment": "spinnaker"
}
```

#### Example Deployment Environments Override

Custom deployment environment order and selection can be provided in the `env`
key. When missing, the default provided is `{"env": ["stage", "prod"]}`. Here,
the order matters and Pipelines will be triggered in the given order.

```json
{
    "deployment": "spinnaker",
    "env": [
        "prod"
    ]
}
```

#### Complete JSON Override

Complete manual overrides can also be provided based on JSON configuration for a
Spinnaker Pipeline, but are not supported. JSON dump can be found in the
Pipeline view.

```json
{
    "deployment": "spinnaker",
    "env": [
        "prod"
    ],
    "prod": {
        "_Custom Spinnaker Pipeline configuration": "Insert here."
    }
}
```

Each deployment environment specified in the `pipeline.json` file will need an
accompanying `application-master-{env}.json` file.

### runway/application-master-{env}.json

To determine which regions to deploy to, a new `regions` key can be used to
override the default of `us-east-1`.

```json
{
    "regions": [
        "us-east-1",
        "us-west-2"
    ]
}
```

## Migration with FIG TODOs

- [ ] Update Pipeline templates to include `gitlab-tagger`
- [ ] Pipeline JSON template did not pick up Jenkins Job
- Update gogo-sauce credentials
  - [x] sox
  - [ ] pci
- [ ] DSL should make Job names lower cased
- [x] S3 Bucket name for sox
- [ ] Have Developers delete current Jenkins Job so Job can be recreated with
  lower casing
- [x] Fix hard coded `desired` ASG
- [x] Manual Judgement: Do you want to proceed and promote the deployment to
  {env}?
- For customers of FIG, dependant services will need access to SOX throug public
