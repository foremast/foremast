from configparser import ConfigParser
from foremast.consts import extract_formats


def test_consts_extract_formats():
    """Test extract_formats()"""

    format_defaults = {
        'domain': 'example.com',
        'app': '{project}',
    }

    config = ConfigParser(defaults=format_defaults)
    config.add_section('formats')

    results = extract_formats(config)
    assert 'example.com' == results['domain']
