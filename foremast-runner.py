#!/usr/bin/env python 

import os
import subprocess

from foremast import *
import gogoutils

class ForemastRunner:

    def __init__(self, token_path=None):
        group_base = os.environ["PROJECT"]
        repo_base = os.environ["GIT_REPO"]
        self.git_project = "{}/{}".format(group_base, repo_base)
        parsed = gogoutils.Parser('$GIT_PROJECT')
        generated = gogoutils.Generator(*parsed.parse_url())
        self.app = generated.app
        self.trigger_job = generated.jenkins()['name']
        self.token_path = token_path


    def run_pipe(name=None, full_command=None):
        splitcmd = full_command.split(" ")
        subprocess.call(splitcmd, shell=True)


# Read application.json files
echo "============================================="
echo " Read application.json"
echo "============================================="
create-configs \
-g "$GIT_PROJECT" \
-t ~/.aws/git.token \
-o ./raw.properties

cat ./raw.properties
echo

# source the file
grep EUREKA ./raw.properties > ./settings.properties
while read -r line; do declare -x "$line"; done < ./settings.properties

echo "============================================="
echo " Create Iam"
echo "============================================="
create-iam \
--app "$APP" \
--env "$ENV"

echo "============================================="
echo " Create S3"
echo "============================================="
create-s3 \
--app "$APP" \
--env "$ENV"

echo "============================================="
echo "Running commands for ${REGION}:${ENV}"
echo "============================================="

# Security Group
echo "============================================="
echo " Create Security Group"
echo "============================================="
create-sg \
--app "$APP" \
--env "$ENV" \
--region "$REGION"

EUREKA="${ENV^^}_APP_EUREKA_ENABLED"
if [[ "${!EUREKA}" != "true" ]]; then

    # Elb
    echo "============================================="
    echo " Create Elb"
    echo "============================================="
    ELB_TYPE=$(jq ".$ENV.elb.subnet_purpose" -r ./raw.properties.json)

    create-elb \
    --app "$APP" \
    --env "$ENV" \
    --region "$REGION"

    # Dns
    echo "============================================="
    echo " Create Dns"
    echo "============================================="
    create-dns \
    --app "$APP" \
    --region "$REGION" \
    --env "$ENV" \
    --elb-subnet "$ELB_TYPE"
else

    echo "============================================="
    echo " Elb and Dns not executed"
    echo "============================================="

fi

echo "============================================="
echo " Send Slack Notification (PROD* only)"
echo "============================================="
slack-notify \
    --env "$ENV" \
    --app "$APP"

echo "============================================="
echo " Clean properties"
echo "============================================="
rm raw.properties
