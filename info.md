## 💽 Version
{% if version_installed == version_available %} 
👍 You already have the latest released version installed. 
{% endif %}

{% if installed and version_installed != selected_tag %}
 🤓 Changes from version {{ version_installed }}
{% endif %}

<h2 align="center">
   <a href="https://www.openmotics.com/en/">OpenMotics</a> and<a href="https://www.home-assistant.io"> Home Assistant</a> integration  🏡 ☀
   </br></br>
   <img src="https://github.com/openmotics/home-assistant/blob/master/pictures/openmotics-logo" >
   </br>
   <a href="https://github.com/hacs/default"><img src="https://img.shields.io/badge/HACS-default-sucess"></a>
    </br>
</h2>

_Component to integrate with [integration_blueprint][integration_blueprint]._

This integration allows visibility and control of the OpenMotics system in Home Assistant. For information about how to configure and the features included in the integration, please see the [Readme.md](https://github.com/openmotics/home-assistant/blob/master/Readme.Md)

{% if not installed %}
## ⚙️ Installation & ♻️ Update

Use hacs.io to manage the installation and update process. 🥳
1. Click install.
2. In the HA UI go to "Configuration" -> "Integrations" click "+" and search for "openmotics".

## ⌨️ Manual installation 

Copy content of `custom_components` folder into your HA `/config/custom_components` folder
{% endif %}

## Configuration is done in the UI

<!---->

---

[integration_blueprint]: https://github.com/openmotics/home-assistant
[commits-shield]: https://img.shields.io/github/commit-activity/y/custom-components/integration_blueprint.svg?style=for-the-badge
[commits]: https://github.com/openmotics/home-assistant/commits/master
[hacs]: https://hacs.xyz
[hacsbadge]: https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge
[discord]: https://discord.gg/Qa5fW2R
[discord-shield]: https://img.shields.io/discord/330944238910963714.svg?style=for-the-badge
[forum-shield]: https://img.shields.io/badge/community-forum-brightgreen.svg?style=for-the-badge
[forum]: https://community.home-assistant.io/
[license]: https://github.com/openmotics/home-assistant/blob/main/LICENSE
[license-shield]: https://img.shields.io/github/license/openmotics/home-assistant.svg?style=for-the-badge
[releases-shield]: https://img.shields.io/github/release/openmotics/home-assistant.svg?style=for-the-badge
[releases]: https://github.com/openmotics/home-assistant/releases
[user_profile]: https://github.com/openmotics
