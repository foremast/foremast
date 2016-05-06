"""Test IAM Policies for correctness."""
import json

from foremast.iam.construct_policy import construct_policy


def test_main():
    """Check general assemblage."""
    settings = {'services': {'s3': True}}
    policy_json = construct_policy(app='coreforrest',
                                   pipeline_settings=settings)

    policy = json.loads(policy_json)

    settings.update({'services': {'dynamodb': ['coreforrest', 'edgeforrest',
                                               'attendantdevops']}})
    policy_json = construct_policy(pipeline_settings=settings)
    policy = json.loads(policy_json)
