# OpenThread Device Management API

This is an API for the management of multiple thread devices in one network

## Requirements

-   PySerial
-   Flask

## Usage

Start the flask server by running

```
flask run
```

The server will start at `127.0.0.1`

## Responses

Each endpoint responds with

```
isError: bool,
statusCode: int,
message: string,
```

and some endpoints will have

```
data: JSON
```

the JSON schema for an endpoint that returns it is specified in the endpoints' section in Endpoints

## Endpoints

### `GET /start`

starts the thread network on each connected device

### `GET /config`

configures the network with 1 router and the rest of the devices as end devices

### `POST /config`

with the argument of

`routers: int`

configures the network with `routers` router and the rest of the devices as end devices. If `routers` is greater than the number of devices on the network, all devices will be configured as routers.

### `GET /state`

gets the state of each device network

Data JSON Schema:

```
[
    {
        port: string,
        state: string,
        rloc: string,
        panid: string,
        channel: string,
        ipaddr: string,
    },
]
```

where `port` or `rloc` can be used as an id

### `GET /stop`

stops the thread network on each device
