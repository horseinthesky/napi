# Overview

`napi` is a concept HTTP controller for network devices.

## 💡 Motivation

So you are a network engineer. You are responsible for a huge multivendor network.

To keep the network secure and easy to manage you want only the networking team to have access to network devices. But related teams (developers/SREs) want to collect data and/or even change network device configuration in some cases.
It is probably not a good idea to manage access for all these external users, their credentials, SSH keys, permissions, etc. Tacacs could be a solution but you still have to set it up and manage it.
And of course, nobody knows the CLI syntax of network boxes and is not eager to learn it. They just want the data!

The main idea of the project is to show how this situation might be solved by establishing a network controller to provide related teams with a familiar HTTP API. It follows [DDD](https://en.wikipedia.org/wiki/Domain-driven_design) approach to keep thing separated, easy to manage, change and extend.

## ✨ Features

- 💪 Easy, secure, and vendor agnostic access your network
- 🚀 Async execution for improved performance powered by [FastAPI](https://fastapi.tiangolo.com/)
- 📊 Multicore load balancing via [Uvicorn](https://www.uvicorn.org/) ASGI web server
- 🔒 Token based authorization
- 📚 Comprehensive API reference via [Swagger](https://swagger.io/) and [Redoc](https://redocly.com/)
- 🎨 Beautiful documentation via [MkDocs](https://www.mkdocs.org/) with [material theme](https://squidfunk.github.io/mkdocs-material/).
- 🛠️ Configurable via `.env` files and `env` variables
- 💾 Completely stateless
