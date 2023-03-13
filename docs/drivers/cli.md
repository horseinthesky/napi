`CLIDriver` is the base async driver class to inherit API drivers from.
::: napi.driver.cli.driver

## Usage

For the best experience, you should inherit `CLIDriver` by your custom API drivers which needs to communicate with network devices via basic SSH cli.

Here is an example of how it is used in the `portswitcher` API.
::: endpoints.portswitcher.driver.cumulus
