class NetconfDriverException(Exception):
    """Base Exception for Netconf driver"""


class Timeout(NetconfDriverException):
    """Exception for netconf driver timeout"""


class ConnectionError(NetconfDriverException):
    """Exception for SSH connection failure"""


class NetconfSessionLimitExceeded(ConnectionError):
    """NETCONF session limit exceeded"""


class AuthError(NetconfDriverException):
    """Exception for SSH auth failure"""


class RPCError(NetconfDriverException):
    """Exception for invalid RPC"""


class CommitError(RPCError):
    """Exception for a specific RPCError: attempt to commit too fast"""


netconf_http_code_map: dict[str, int] = {
    "Timeout": 522,
    "ConnectionError": 523,
    "AuthError": 511,
    "RPCError": 400,
    "CommitError": 507,
    "NetconfSessionLimitExceeded": 509,
}
