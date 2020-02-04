## Wireless Multihop Network
<!-- ALL-CONTRIBUTORS-BADGE:START - Do not remove or modify this section -->
[![All Contributors](https://img.shields.io/badge/all_contributors-1-orange.svg?style=flat-square)](#contributors-)
<!-- ALL-CONTRIBUTORS-BADGE:END -->

An implementation of a network:
- Wireless (Using Bluetooth)
- Decentralized (the full network topology is _eventually_ known at every node)
- Multi-hop (no direct connection required between end-users, a path is sufficient)
- Auto network discovery (for joining) & disconnection handling (updating the state of the network and informing the network) 
- Routing & forwarding using Dijkstra Shortest Path (all connection assumed the same weight)

The demonstration application is a chatting application that supports a dynamic number of users.
The project is a part of the postgraduate course at the GUC (_CSEN 1066: Selected Topics in Communication Networks project_)

## Requirements

### System Dependancies
```bash
sudo apt-get install libbluetooth-dev
```

### Python packages

```bash
pip install pybluez pexpect inquirer
```

- [pybluez](https://github.com/pybluez/pybluez)
- [pexpect](https://github.com/pexpect/pexpect) (used by the bluetoothctl command wrapper)

### Configuration

To allow the use of 'services' in bluetooth, edit `/etc/systemd/system/dbus-org.bluez.service` and change: 
```
ExecStart=/usr/lib/bluetooth/bluetoothd
```
To
```
ExecStart=/usr/lib/bluetooth/bluetoothd --compat
```
Then restart the bluetooth: 
```bash
sudo systemctl daemon-reload
sudo systemctl restart bluetooth
```

You'll need to run the application as `sudo` for the correct permissions.

## Contributors ✨

Thanks goes to these wonderful people ([emoji key](https://allcontributors.org/docs/en/emoji-key)):

<!-- ALL-CONTRIBUTORS-LIST:START - Do not remove or modify this section -->
<!-- prettier-ignore-start -->
<!-- markdownlint-disable -->
<table>
  <tr>
    <td align="center"><a href="http://amrmkayid.github.io"><img src="https://avatars1.githubusercontent.com/u/18689888?v=4" width="100px;" alt=""/><br /><sub><b>Amr M. Kayid</b></sub></a><br /><a href="https://github.com/AbdullahKady/wireless-multihop-network/commits?author=AmrMKayid" title="Code">💻</a></td>
  </tr>
</table>

<!-- markdownlint-enable -->
<!-- prettier-ignore-end -->
<!-- ALL-CONTRIBUTORS-LIST:END -->

This project follows the [all-contributors](https://github.com/all-contributors/all-contributors) specification. Contributions of any kind welcome!