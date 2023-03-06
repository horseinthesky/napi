class ScrapliDriverException(Exception):
    '''Base Exception for Scrapli driver'''


class Timeout(ScrapliDriverException):
    '''Exception for cli driver timeout'''


class ConnectionError(ScrapliDriverException):
    '''Exception for SSH connection failure'''


class AuthError(ScrapliDriverException):
    '''Exception for SSH auth failure'''


class UnsupportedVendor(ScrapliDriverException):
    '''Unsupported vendor for Scrapli connection'''


CLI_HTTP_CODE_MAP = {
    'Timeout': 522,
    'ConnectionError': 523,
    'AuthError': 511,
    'UnsupportedVendor': 405,
}
