"""Test S3 tags result."""
from foremast.utils import generate_s3_tags


def test_s3_tags_data():
    """Result data should be list then needs to have Key:key Value:value format."""
    test_result = generate_s3_tags.generated_tag_data({'app_group': 'test_value'})

    assert list == type(test_result)
    assert 'app_group' == test_result[0]['Key']
    assert 'test_value' == test_result[0]['Value']
