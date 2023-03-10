import asyncio
from dataclasses import dataclass
from functools import partial
from typing import Any, Self

from scrapli import AsyncScrapli
from scrapli.driver import AsyncGenericDriver
from scrapli.exceptions import ScrapliAuthenticationFailed, ScrapliConnectionError, ScrapliTimeout

from napi.driver.lib import transform

from . import constants, exceptions

cmdify = partial(transform, attr="to_cmd")


@dataclass
class CLIDriver:
    """
    CLIDriver is the base async driver class to inherit API drivers from.

    It provides basic methods send_command and  send_commands to execute one or many commands in the devices shell.
    It is best for API driver to inherit from CLIDriver and use its methods as part of technical implementation
    of API business logic.

    Args:
        host: host ip/name to connect to
        vendor: the network device manufacturer
        timeout: SSH connection timeout

    Returns:
        None

    Raises:
        N/A
    """

    host: str
    vendor: str
    timeout: int = 15

    async def __aenter__(self) -> Self:
        """
        Enter method for context manager. Opens SSH connection.

        Args:
            N/A

        Returns:
            Self: an instance of CLIDriver

        Raises:
            N/A
        """
        await self.connect()
        return self

    async def __aexit__(self, *_) -> None:
        """
        Exit method to cleanup for context manager. Closes SSH connection.

        Args:
            exception_type: exception type being raised
            exception_value: message from exception being raised
            traceback: traceback from exception being raised

        Returns:
            None

        Raises:
            N/A
        """
        await self.disconnect()

    async def connect(self) -> None:
        """
        Open SSH connection

        Args:
            N/A

        Returns:
            None

        Raises:
            Timeout: timeout is exceeded
            ConnectionError: failed to establish connection
            AuthError: failed to authenticate on network device
        """
        self._connection = self._setup_connection()

        try:
            await self._connection.open()
        except ScrapliTimeout:
            raise exceptions.Timeout(f"Connection to {self.host} timed out")
        except ScrapliConnectionError as e:
            raise ConnectionError(f"{str(e)}")
        except ScrapliAuthenticationFailed:
            raise exceptions.AuthError(f"Failed to authenticate on {self.host}")

        await asyncio.sleep(0.3)

    async def disconnect(self) -> None:
        """
        Close SSH connection

        Args:
            N/A

        Returns:
            None

        Raises:
            N/A
        """
        await self._connection.close()

    async def send_command(self, command: str) -> str:
        """
        Execute one command in the device shell

        Args:
            command: actual command

        Returns:
            str: response from the device

        Raises:
            N/A
        """
        return (await self._connection.send_command(command)).result

    @cmdify(param="cmds")
    async def send_commands(self, cmds: list[str]) -> str:
        """
        Execute a listr of command in the device shell

        Args:
            cmds: a list of commands to execute

        Returns:
            str: response from the device

        Raises:
            N/A
        """
        return (await self._connection.send_commands(cmds)).result

    def _setup_connection(self) -> AsyncScrapli | AsyncGenericDriver:
        """
        Setup the correct scrapli class as CLI driver

        Args:
            None

        Returns:
            AsyncScrapli | AsyncGenericDriver: corresponding scrapli driver

        Raises:
            UnsupportedVendor: provided vendor is not supported
        """
        params = {
            "host": self.host,
            "auth_username": constants.username,
            "auth_private_key": constants.ssh_key,
            "transport": "asyncssh",
            "auth_strict_key": False,
            "timeout_transport": self.timeout,
        }

        driver_map: dict[str, Any] = {
            "huawei": {
                "driver": AsyncScrapli,
                "params": {
                    "platform": "huawei_vrp",
                    **params,
                },
            },
            "nvidia": {
                "driver": AsyncGenericDriver,
                "params": params,
            },
        }

        driver_config = driver_map.get(self.vendor)
        if not driver_config:
            raise exceptions.UnsupportedVendor(
                f"Unsupported vendor {self.vendor} of host {self.host} for connection"
            )

        return driver_config["driver"](**driver_config["params"])
