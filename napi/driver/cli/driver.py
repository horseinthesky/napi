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
    host: str
    vendor: str
    timeout: int = 15

    async def __aenter__(self) -> Self:
        await self.connect()
        return self

    async def __aexit__(self, *_) -> None:
        await self.disconnect()

    async def connect(self) -> None:
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
        await self._connection.close()

    async def send_command(self, command: str) -> str:
        return (await self._connection.send_command(command)).result

    @cmdify(param="cmds")
    async def send_commands(self, cmds: list[str]) -> str:
        return (await self._connection.send_commands(cmds)).result

    def _setup_connection(self) -> AsyncScrapli | AsyncGenericDriver:
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
