Home Assistant OpenMotics plugin
==============================================================================================================================================================================================

Home Assistant is a home automation platform running on Python 3. It is able to track and control all devices at home and offer a platform for automating control.

To get started: Check out `home-assistant.io <https://home-assistant.io>`

.. code:: bash

    cd /home/home-assistant/.home-assistant
    mkdir OpenMotics
    git clone https://github.com/woutercoppens/home-assistant.git OpenMotics
    
    cd /srv/homeassistant/lib/python3.6/site-packages/homeassistant/components/
    ln -s /home/homeassistant/.homeassistant/OpenMotics/openmotics.py .
    ln -s /home/homeassistant/.homeassistant/OpenMotics/switch/openmotics.py switch/
    ln -s /home/homeassistant/.homeassistant/OpenMotics/light/openmotics.py light/

Add this to configuration.yaml:
  openmotics:
   username: xxxx
   password: xxxx
   host: xxxx
   
Host can be local hostname, local ip address, openmotics.local or cloud.openmotics.com
If you're using local hostname or ip, you have to create a local user in the OpenMotics Gateway.

