NetconfDriver is the base async driver class to inherit API drivers from.
::: napi.driver.netconf.driver

## Usage

NetconfDriver is inherited by custom API drivers which needs to communicate with network devices via NETCONF protocol.

Here is an example of how it is used in the `portswitcher` API.
::: endpoints.portswitcher.driver.ce
