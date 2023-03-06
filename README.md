# napi
`napi` is a concept HTTP controller for network devices.

## 💡 Motivation

So you are a network engineer. You are responsible for a huge multivendor network.

To keep the network secure and easy to manage you want only the networking team to have access to network devices. But related teams (developers/SREs) want to collect data and/or even change network device configuration in some cases.
It is probably not a good idea to manage access for all these external users, their credentials, SSH keys, permissions, etc. Tacacs could be a solution but you still have to set it up and manage it.
And of course, nobody knows the CLI syntax of network boxes and is not eager to learn it. They just want the data!

The main idea of the project is to show how this situation might be solved by establishing a network controller to provide related teams with a familiar HTTP API. It follows [DDD](https://en.wikipedia.org/wiki/Domain-driven_design) approach to keep thing separated, easy to manage, change and extend.

## ✨ Features

- 💪 High level vendor agnostic access to network devices
- 🚀 Async execution for improved performance powered by [FastAPI](https://fastapi.tiangolo.com/)
- 📊 Multicore load balancing via [Uvicorn](https://www.uvicorn.org/) ASGI web server
- 🔒 Token based authorization
- 📚 Beautiful and comprehensive docs via [Swagger](https://swagger.io/) and [Redoc](https://redocly.com/)
- 🛠️ Configurable via `.env` files and `env` variables
- 💾 Completely stateless

## 🔎 Internals

`napi` provides three main building blocks to solve any task you might imagine:
- token authorization
- inventory system
- network drivers

### 🔒 Authorization

Authorization module uses static tokens but you can easily extend it to support [JWT](https://jwt.io/) or [PASETO](https://paseto.io/).

`auth.yml` has one user `user1` with a `token` token to show the structure of user permissions.

You can generate new user tokens with this code snippet:

```
In [1]: import secrets, hashlib

In [2]: token = secrets.token_hex(16)

In [4]: token
Out[4]: 'bf3ae64635504b9b4ce71a6c7ab2bc8c'

In [5]: hashlib.sha256(token.encode('utf-8')).hexdigest()
Out[5]: '95fabfb1713ea5abb54767b2bea0fe49bbd29faad610df7c58c796408a29e7a5'
```

Hash is stored in `auth.yml` file to authorize the corresponding user.

### 📋 Inventory

Inventory module is designed to work with SoT (Source of Truth) systems. By default it has [Netbox](https://docs.netbox.dev/en/stable/) support. You can find an example DB for it in an `examples` folder.

As an example it has `Device`, `Interface` and `SupportsGetDeviceInterface` abstractions to make support of other systems a breese.

### 🔌 Drivers

Drivers module provides drivers to interact with network devices via CLI or [NETCONF](https://en.wikipedia.org/wiki/NETCONF) protocol:
- CLI driver is powered by [Carl Montanari](https://www.montanari.io/)'s amazing [scrapli](https://github.com/carlmontanari/scrapli) library.
- NETCONF driver is powered by robust [asyncssh](https://asyncssh.readthedocs.io/en/latest/) library with in-house wrapper to make in NETCONF ready.

## 💻 Endpoints

As proof of concept `napi` provides a few endpoints:
- `ping` - simple availability endpoint to put under your load balancer or k8s health check
- `portswitcher` - reconfigures DC fabric leaf switch downlinks (server-faced interfaces)
- `macgrabber` - gets switch MAC addresses

### Ping

Always responds with:

```
{
  "code": 200,
  "status": "ok"
}
```

### Portswitcher

`portswitcher` is an example of how you can provide an easy vendor agnostic way for your related teams to get/change a network device configuration (L2 interfaces is this case).

It works the same way with blackbox and whitebox switches. Example supports Huawei CE (Cloud Engine) switches and Nvidia Mellanox switches.

#### GET

It expects input data describing the network device interface:

```
{
  "switch": "string",
  "interface": "string"
}
```

And returns an abstracted interface "state" - `prod`/`setup`:

```
{
  "code": 200,
  "status": "ok",
  "result": {
    "switch": "string",
    "interface": "string",
    "state": "prod"
  }
}
```

These `prod`/`setup` states are the combination of interface mode (access/trunk) and VLANS on the interface. Check the DB example to see the details.

#### POST

In the same way POST expects data describing the interface plus the desired "state":

```
{
  "switch": "string",
  "interface": "string",
  "state": "prod"
}
```

The response is just the same as for GET:

```
{
  "code": 0,
  "status": "ok",
  "result": {
    "switch": "string",
    "interface": "string",
    "state": "prod"
  }
}
```


## 📈 Usage

To try it out clone the repo:

```
git clone https://github.com/horseinthesky/napi.git
```

Next install dependencies ([poetry](https://python-poetry.org/) is required):

```bash
make setup
```

And finally run `napi` server:

```bash
make run
```

### 🛠️ Configuration

Configuration is managed by [pydantic](https://docs.pydantic.dev/)'s [Settings](https://docs.pydantic.dev/usage/settings/) module.

You must have `.env` file to setup the following settings:
- **nv_api_url** (`NV_API_URL` env var) - an address of Netbox API
- **tenants** (`TENANTS` env var) - comma separated list of tenants network devices belong to in SoT
- **domains** (`DOMAINS` env var) - comma separated list of domains network devices has their fqnds from
- **endpoints** (`ENDPOINTS` env var) - comma separated list of endpoints to use in the environment

Each setting must be prefixed with the corresponding "environment" value. Both in `.env` file AND as env variable.

By default `napi` runs in `prod` environment. It is controlled by `ENV` env variable.

Here is an example `.env` file from the repo:

```
prod_nb_api_url=http://localhost:8000/api
prod_tenants=production
prod_domains=local
prod_endpoints=portswitcher,macgrabber
```
