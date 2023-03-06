import asyncio
from copy import deepcopy
from dataclasses import dataclass, field
from functools import partial
from typing import Any, Self

import asyncssh
import xmltodict

from napi.driver.lib import transform
from napi.logger import core_logger as logger

from . import constants, exceptions, rpcs

asyncssh.set_debug_level(1)

asdictify = partial(transform, attr="as_dict")


@dataclass
class NetconfDriver:
    host: str
    timeout: int = 5
    capabilities: list[str] = field(default_factory=lambda: rpcs.capabilities)

    async def __aenter__(self) -> Self:
        await self.connect()
        return self

    async def __aexit__(self, *exception) -> None:
        self.disconnect()

    async def connect(self) -> None:
        try:
            self._connection = await asyncio.wait_for(
                asyncssh.connect(
                    self.host,
                    known_hosts=None,
                    username=constants.username,
                    client_keys=constants.ssh_keys,
                    kex_algs=["ecdh-sha2-nistp256"],
                    server_host_key_algs=["ssh-rsa"],
                    encryption_algs=["aes128-ctr"],
                    mac_algs=["hmac-sha2-256"],
                    compression_algs=["none"],
                ),
                timeout=self.timeout,
            )
        except asyncio.exceptions.TimeoutError as e:
            logger.critical(repr(e), exc_info=True)
            raise exceptions.Timeout(f"Connection to {self.host} timed out")
        except (asyncssh.misc.KeyExchangeFailed, asyncssh.misc.ProtocolError) as e:
            logger.critical(repr(e), exc_info=True)
            raise exceptions.ConnectionError(f"{str(e)}")
        except asyncssh.misc.ConnectionLost as e:
            logger.critical(repr(e), exc_info=True)
            raise exceptions.ConnectionError(f"Lost connection to {self.host}")
        except ConnectionRefusedError as e:
            logger.critical(repr(e), exc_info=True)
            raise exceptions.ConnectionError(f"Failed to connect to {self.host}")
        except asyncssh.misc.PermissionDenied as e:
            logger.critical(repr(e), exc_info=True)
            raise exceptions.AuthError(f"Failed to authenticate on {self.host}")
        except Exception as e:
            logger.critical(repr(e), exc_info=True)
            raise

        try:
            self._writer, self._reader, _ = await self._connection.open_session(subsystem="netconf")
        except asyncssh.misc.ChannelOpenError:
            raise exceptions.ConnectionError(f"Connection to {self.host} refused by host")

        await self._read()
        self._hello()
        await asyncio.sleep(0.01)

    def disconnect(self) -> None:
        self._write(rpcs.close)
        self._connection.close()

    def _hello(self) -> None:
        payload: dict[str, Any] = deepcopy(rpcs.hello)
        payload["hello"]["capabilities"]["capability"] = self.capabilities
        self._write(payload)

    async def _read(self) -> dict[str, Any]:
        rpc_reply = await self._reader.readuntil("]]>]]>")
        logger.debug(f"_read {rpc_reply}")

        rpc_reply_data = xmltodict.parse(rpc_reply[:-6], dict_constructor=dict)
        reply = rpc_reply_data["rpc-reply"] if "rpc-reply" in rpc_reply_data else None
        if reply is not None and "rpc-error" in reply:
            if isinstance(reply["rpc-error"], list):
                message = reply["rpc-error"][0]["error-message"]
            else:
                message = reply["rpc-error"]["error-message"]

            if isinstance(message, dict) and "#text" in message:
                text = message["#text"]

                if "The system is busy in committing configurations of other users" in text:
                    raise exceptions.CommitError(text)

                raise exceptions.RPCError(text)

            raise exceptions.RPCError(reply["rpc-error"]["error-message"])

        return rpc_reply_data

    def _write(self, data) -> None:
        xml_data = xmltodict.unparse(data, full_document=False, pretty=True) + "]]>]]>"
        logger.debug(f"_write {xml_data}")

        self._writer.write(xml_data)

    @asdictify(param="filter_")
    async def get(self, *, filter_: dict[str, Any] | None = None) -> dict[str, Any]:
        payload: dict[str, Any] = deepcopy(rpcs.get)

        if filter_ is not None:
            payload["rpc"]["get"]["filter"] = {
                "@type": "subtree",
                **filter_,
            }

        self._write(payload)
        return await self._read()

    @asdictify(param="filter_")
    async def get_config(
        self, *, source="running", filter_: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        payload: dict[str, Any] = deepcopy(rpcs.get_config)
        payload["rpc"]["get-config"]["source"] = {source: None}
        if filter_ is not None:
            payload["rpc"]["get-config"]["filter"] = {
                "@type": "subtree",
                **filter_,
            }

        self._write(payload)
        return await self._read()

    @asdictify(param="config")
    async def edit_config(self, *, target="running", config: dict[str, Any]) -> dict[str, Any]:
        payload: dict[str, Any] = deepcopy(rpcs.edit_config)
        payload["rpc"]["edit-config"] = {
            "target": {target: None},
            "config": {**config},
        }

        self._write(payload)
        return await self._read()
