"""Generate various filenames."""

def generate_packer_filename(provider, region, builder):
    """Generate a filename to be used by packer.

    Args:
        provider (str): Name of Spinnaker provider.
        region (str): Name of provider region to use.
        builder (str): Name of builder process type.

    Returns:
        str: Generated filename based on parameters.
    """
    filename = '{0}_{1}_{2}.json'.format(provider, region, builder)
    return filename
