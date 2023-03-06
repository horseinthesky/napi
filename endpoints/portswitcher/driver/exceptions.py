class PortSwitcherException(Exception):
    '''PortSwitcher base exception'''


class ConfigurationError(PortSwitcherException):
    '''Exception for config issues'''


portswitcher_http_code_map: dict[str, int] = {
    'ConfigurationError': 400,
}
