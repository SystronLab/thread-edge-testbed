## Attack Scenario
An attacker has a device that is able to detect network activity, and a device that can inject packets onto a network. Using the activity monitor the attacker is able to find the channel with the highest level of activity, and uses this to specify which channel to inject packets onto, reasoning that the channel has a network on it that the attacker wants to bring down.

## Equipment
The activity monitor is a Nordic Semiconductor Development Board, using the OpenThread Network Scanning functionality to detect the energy level on the the channels. The packet injector is a Sewio OpenSniffer, configured to inject valid IEEE 802.15.4 packets onto the specified channel with an IFS of 1ms, saturating the network.

