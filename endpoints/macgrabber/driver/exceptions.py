class MacGrabberException(Exception):
    '''MacGrabber base exception'''


class ConfigurationError(MacGrabberException):
    '''Exception for config issues'''


macgrabber_http_code_map: dict[str, int] = {
    'ConfigurationError': 400,
}
