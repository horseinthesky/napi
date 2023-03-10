# Usage

## ⚡️ Requirements

Before running `napi` you need to setup source of thuth (SoT) - an inventory system. By default it has only [Netbox](https://docs.netbox.dev/en/stable/) support build in.

You can set it up on your own installation or use a [community solution](https://github.com/netbox-community/netbox-docker).

Don't forget to change view permissions to get full read access without a token by setting:

```
EXEMPT_VIEW_PERMISSIONS = ['*']
```

in `configuration/configuration.py` file.

And then run:

```
docker-compose up -d
```

After Netbox is started load example DB from `examples/db_dump.sql.gz` with the following command:

```
gunzip -c db_dump.sql.gz | docker-compose exec -T postgres sh -c 'psql -U $POSTGRES_USER $POSTGRES_DB'
```

Now you are ready to try it out.

## 📚 Clone

To try it out clone the repo:

```
git clone https://github.com/horseinthesky/napi.git
```

Next install dependencies ([poetry](https://python-poetry.org/) is required):

```bash
make setup
```

## 🛠️ Configuration

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

## 🚀 Run

Finally run `napi` server:

```bash
make run
```

By default it runs on port **8080** with several workers (number calculated via `nproc`).
