# OpenThread Device Management Console

This is a CLI console for management of multiple thread devices in one network.

## Requirements

-   PySerial

## Assumptions

-   All thread devices are running the open thread CLI and are capable of communication through a COM port
-   All thread devices have `Zephyr` or `ESR32` as their platform (see Usage for adding other platforms)

## Usage

Once launched run commands listed in the Commands section to control the thread network. To simply start a network run:

```
>config
>start
```

This will start a thread network from the connected thread devices, with one device being automatically assigned router status.

The state of the network can then be viewed with

```
>state
```

This will display the status of each device (detailed under `state` in commands below) as well as the IP address and COM port it is connected to.

The network can be stopped with

```
>stop
```

The network will also stop upon quitting the console, with either `quit` or a keyboard interrupt (Ctrl + C)

### Adding other platforms:

To interact with devices of another platform run the `platform` command in the function `link_devices()` following the ESR32 and Zephyr platform examples. If a prefix is required for interacting with the CLI for that platform (e.g. adding `ot ` to the beginning of commands for Zephyr based devices) then add functionality for that in `ot_device.run_command(command)`.

## Commands

### config n

Sets the datasets of the devices so that they connect to the same network:

```
channel: 15
panid: 0xabcd
networkkey: 00112233445566778899aabbccddeeff
```

Also sets `ifconfig` to `up`, and gets the IP address of each device.

A integer parameter can be passed here to choose how many devices are set up as routers. Default is 1. If the number passed is higher than the number of devices on the network then all devices will be routers.

### start

Starts the thread network on each device

### stop

Stops the thread network on each device

### state

Check the state of all devices in the thread network. Will provide one of

-   `disabled`
-   `detached`
-   `child`
-   `router`
-   `leader`
-   `unknown`

for each device connected.

### info

Expands on state, giving PAN ID, Network Key, Channel, IP Address and RSSI

### rssi

Gives the recieved signal strength indicator for the device on the current channel it is operating on

## Demos

Pre configured demonstration events for testing that the system is working.

### Ping

Usage: `demo ping`
Pings all devices from every other device on the network, reporting any dropped packets. Any drop rate above 0.0% is considered a fail in this demonstration - all devices on the network must be able to communicate with one another, and only one packet is being sent from each device.

## Debug Flag

If the `DEBUG` flag is set to `True`, then extra info will be outputted whilst running, including:

-   Every command sent to each device, and the full response from each device (formatted to separate responses by device)
-   The available serial connections found by the program
-   The full rloc response for each device
