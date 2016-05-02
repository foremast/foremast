"""Package constants."""
API_URL = 'http://gate-api.build.example.com:8084'
GIT_URL = 'https://github.com'
HEADERS = {
    'accept': '*/*',
    'content-type': 'application/json',
    'user-agent': 'foremast',
}
LOGGING_FORMAT = ('%(asctime)s [%(levelname)s] %(name)s:%(funcName)s:'
                  '%(lineno)d - %(message)s')
