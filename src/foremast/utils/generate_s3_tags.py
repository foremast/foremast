"""S3 Tag functions."""


def generated_tag_data(tags):
    """Convert :obj:`dict` to S3 Tag list.

    Args:
        tags (dict): Dictonary of tag key and tag value passed.

    Returns:
        list: List of dictionaries.

    """
    generated_tags = []
    for key, value in tags.items():
        generated_tags.append({
            'Key': key,
            'Value': value,
        })
    return generated_tags
