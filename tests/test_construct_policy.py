"""Test IAM Policies for correctness."""
import json

from foremast.iam.construct_policy import construct_policy

ANSWER1 = {
    'Version': '2012-10-17',
    'Statement': [
        {
            'Effect': 'Allow',
            'Action': [
                's3:GetObject',
                's3:ListObject'
            ],
            'Resource': [
                'arn:aws:s3:::archaius-stage/forrest/unicornforrest',
                'arn:aws:s3:::archaius-stage/forrest/unicornforrest/*'
            ]
        }
    ]
}


def test_iam_construct_policy():
    """Check general assemblage."""
    settings = {}

    policy_json = construct_policy(pipeline_settings=settings)
    assert policy_json is None

    settings = {'services': {'s3': True}}
    policy_json = construct_policy(app='unicornforrest',
                                   env='stage',
                                   group='forrest',
                                   pipeline_settings=settings)

    assert json.loads(policy_json) == ANSWER1

    # TODO: Test other services besides S3
    settings.update({'services': {'dynamodb': ['coreforrest', 'edgeforrest',
                                               'attendantdevops']}})
    policy_json = construct_policy(pipeline_settings=settings)
    policy = json.loads(policy_json)
