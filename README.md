# Home Assistant - OpenMotics plugin

Home Assistant is a home automation platform running on Python 3. It is able to track and control all devices at home and offer a platform for automating control.

## Contribute

This plugin is a community effort and OpenMotics cannot give any warranties even though you can report any issues and we'll help as much as possible. Pull requests are always welcome.

## Getting started

To get started: Check out `home-assistant.io <https://home-assistant.io>`
Clone this repo into custom_components

```
cd /home/home-assistant/.home-assistant
mkdir -p custom_components/openmotics
cd custom_components
git clone https://github.com/openmotics/home-assistant.git openmotics
or
git clone -b dev https://github.com/openmotics/home-assistant.git openmotics
```


Add this to configuration.yaml:
```
openmotics:
  client_id: xxxx
  client_secret: xxxx
  host: xxxx (Optional)
```

Host can be local hostname, local ip address, `openmotics.local` or `cloud.openmotics.com`. If you're using local hostname or ip, you have to create a local user in the OpenMotics Gateway.
If host is omitted, it connects by default to cloud.openmotics.com.

## License

This project is licensed under the AGPLv3 License - see the [LICENSE.md](LICENSE.md) file for details

## Acknowledgments

* Special thanks to @woutercoppens for making this plugin and donating it to OpenMotics.
