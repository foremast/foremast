"""Verify AWS Lambda Event creation."""
import copy
from unittest import mock

from foremast.awslambda.awslambdaevent import LambdaEvent

TRIGGERS_MULTIPLE_FILTER = [
    {
        "type": "s3",
        "bucket": "my.shared.bucket",
        "events": [
            "s3:ObjectCreated:*"
        ],
        "prefix": "",
        "suffix": ".json"
    },
    {
        "type": "s3",
        "bucket": "my.shared.bucket",
        "events": [
            "s3:ObjectCreated:*"
        ],
        "prefix": "",
        "suffix": ".tar.gz"
    }
]

TRIGGERS_BUCKET_A = [
    {
        "type": "s3",
        "bucket": "my.shared.bucket",
        "events": [
            "s3:ObjectCreated:*"
        ],
        "prefix": "",
        "suffix": ".json"
    }
]

TRIGGERS_BUCKET_B = [
    {
        "type": "s3",
        "bucket": "my.other.shared.bucket",
        "events": [
            "s3:ObjectCreated:*"
        ],
        "prefix": "",
        "suffix": ".tar.gz"
    }
]

def get_properties_with_triggers(triggers):
    return {
        'app': {
            'lambda_memory': 0,
            'lambda_timeout': 0,
            'lambda_environment': None,
            'lambda_layers': None,
            'lambda_dlq': None,
            'lambda_tracing': None,
            'lambda_destinations': None,
            'lambda_subnet_count': None,
            'lambda_filesystems': None,
            'lambda_provisioned_throughput': None
        },
        "lambda_triggers": triggers
    }

@mock.patch('foremast.awslambda.s3_event.s3_event.add_lambda_permissions')
@mock.patch('foremast.awslambda.s3_event.s3_event.get_lambda_alias_arn')
@mock.patch('foremast.awslambda.s3_event.s3_event.boto3')
@mock.patch('foremast.awslambda.awslambdaevent.remove_all_lambda_permissions')
@mock.patch('foremast.awslambda.awslambdaevent.create_s3_event')
@mock.patch('foremast.awslambda.awslambdaevent.get_properties')
def test_create_s3_event_multiple_filters(mock_get_properties, mock_create_s3_event, mock_remove_perms, mock_boto3, mock_arn, mock_perms):
    """Try to create a lambda with two s3 triggers from the same bucket."""
    triggers = TRIGGERS_MULTIPLE_FILTER
    properties = get_properties_with_triggers(TRIGGERS_MULTIPLE_FILTER)
    mock_get_properties.return_value = properties
    mock_arn.return_value = 'fake_arn'

    events = LambdaEvent(app='test_app', env='test_env', region='us-east-1', prop_path='other')
    events.create_lambda_events()

    mock_create_s3_event.assert_called_with(app_name='test_app', env='test_env', region='us-east-1', bucket='my.shared.bucket', triggers=triggers)

@mock.patch('foremast.awslambda.s3_event.s3_event.add_lambda_permissions')
@mock.patch('foremast.awslambda.s3_event.s3_event.get_lambda_alias_arn')
@mock.patch('foremast.awslambda.s3_event.s3_event.boto3')
@mock.patch('foremast.awslambda.awslambdaevent.remove_all_lambda_permissions')
@mock.patch('foremast.awslambda.awslambdaevent.create_s3_event')
@mock.patch('foremast.awslambda.awslambdaevent.get_properties')
def test_create_s3_event_multiple_buckets(mock_get_properties, mock_create_s3_event, mock_remove_perms, mock_boto3, mock_arn, mock_perms):
    """Try to create a lambda with two S3 triggers from different buckets."""

    triggers = TRIGGERS_BUCKET_A + TRIGGERS_BUCKET_B
    properties = get_properties_with_triggers(triggers)
    mock_get_properties.return_value = properties
    mock_arn.return_value = 'fake_arn'

    events = LambdaEvent(app='test_app', env='test_env', region='us-east-1', prop_path='other')
    events.create_lambda_events()

    s3_calls = [
        mock.call(app_name='test_app', env='test_env', region='us-east-1', bucket='my.shared.bucket', triggers=TRIGGERS_BUCKET_A),
        mock.call(app_name='test_app', env='test_env', region='us-east-1', bucket='my.other.shared.bucket', triggers=TRIGGERS_BUCKET_B)
    ]

    mock_create_s3_event.assert_has_calls(s3_calls, any_order=True)
