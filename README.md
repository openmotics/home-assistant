# OpenMotics Home Assistant integration Beta

**BETA WARNING: this Beta release contains a significant amount of changes to support Outputs, Lights, Scenes and Shutters for the OpenMotics Gateway. It equally uses v0.0.1 of the pyHAopenmotics API, which also contains a significant amount of changes.  It has been tested but may contain some bugs in existing or new functionality.  Use in your live environment at your own risk.**

This repository contains a Home Assistant component + platforms, for the awesome OpenMotics solution.

For the latest version of the OpenMotics Home Assistant Platform please use the master branch or better still install via HACS. if you want bleeding edge then checkout the dev branch, or look out for beta releases via HACS. Depending on what you choose you may need to use the Manual Code Installation described below.

<!-- TOC -->

- [OpenMotics Home Assistant integration Beta](#openmotics-home-assistant-integration-beta)
  - [INTRODUCTION](#introduction)
  - [Minimum Requirements](#minimum-requirements)
  - [HOW TO INSTALL](#how-to-install)
    - [1. Grant permissions to your OpenMotics installation](#1-grant-permissions-to-your-openmotics-installation)
    - [2. Install Home Assistant Core](#2-install-home-assistant-core)
    - [3. Install the custom integration](#3-install-the-custom-integration)
    - [4. Configure the integration.](#4-configure-the-integration)
- [Run, Play](#run-play)
- [License](#license)
- [Acknowledgments](#acknowledgments)

<!-- /TOC -->

## INTRODUCTION

This custom component is developed for controlling an [OpenMotics](https://www.openmotics.com/en/) platform by using the pyHAopenmotics sdk.

## Minimum Requirements

Requires a minimum of HA 2022.03.  This is needed to support the new functionality and changes to config flow.
Requires the new pyHAopenmotics v0.0.1 (or newer) sdk.

## HOW TO INSTALL

### 1. Grant permissions to your OpenMotics installation

Login to [cloud.openmotics.com](https://cloud.openmotics.com/)

![login](/pictures/login.cloud.openmotics.com.png)

Remember to use your e-mail address as login.

Make sure your installation is at a recent firmware. Update if needed.

![firmware](/pictures/update01.png)

Create an additional user

![user01](/pictures/user01.png)

![user02](/pictures/user02.png)

Note: Since the last update of the webui, the link to the integrations is missing. You can access it directly via:
[https://portal.openmotics.com/#cloud/oauth](https://portal.openmotics.com/#cloud/oauth)

![user03](/pictures/user03.png)

![user04](/pictures/user04.png)

Make sure the Client type is `Confidential` and the Grant type is `Client credentials`.
The Redirect URI is not used right now and can have any value.

![user05](/pictures/user05.png)

Copy the Client ID and Client secret as you'll need it to configure the integration in Home Assistant.

### 2. Install Home Assistant Core

See [Home Assistant Official Installation Guide](https://www.home-assistant.io/installation/) to install Home Assistant Core.

### 3. Install the custom integration

We highly recommend using [HACS Home Assistant Community Store](https://github.com/hacs), for more information on how to install HACS please see their documentation website at https://hacs.xyz/

Option 1: HACS installation

1. See [HACS Official Installation Guide](https://hacs.xyz/docs/installation/installation/) and install HACS.
2. See [Initial Configuration Guide](https://hacs.xyz/docs/configuration/basic) and complete initial configuration.
3. Open Home Assistant. Click HACS > Integrations > ⋮ > Custom repositories.

![custom repository](/pictures/hacs_custom_repositories.png)

4. Enter `https://github.com/openmotics/home-assistant` in the address bar at the bottom left of the window. Select Integration from the Category list and click ADD.

![github](/pictures/hacs_add_repository.png)

![new_repository](/pictures/hacs_new_repository.png)

5. Click the new repositry. In the dialog box that appears, click DOWNLOAD THIS REPOSITORY WITH HACS.

![install](/pictures/hacs_download_repository.png)

Option 2:  Manual Code Installation

This method is best used when you want to play with the "latest and greatest" from the repository. Moving forward, the github repository will contain two primary branches, **master** and dev. Master is the latest released, and hopefully most stable branch, whereas **dev** is the branch that we're currently working on.


1. Download the [openmotics-home-assistant repo](https://github.com/openmotics/home-assistant).
2. Unzip it and copy the `custom_components/openmotics` folder to the Home Assistant configuration directory, for example `~/.homeassistant`.

![configuration directory](/pictures/copy_method.png)

The disadvantage of a manual installation is that you won't be notified about updates.

### 4. Configure the integration.

Make sure you restart Home Assistant after the installation (in HACS). After the restart, go to **Configuration** in the side menu in Home Assistant and select **Integrations**. Click on **Add Integrations** in the bottom right corner and search for **Openmotics** to install. This will open the configuration menu with the default settings.

![New Integration](/pictures/new_integration.png)

![Integration setup](/pictures/integration_setup.png)

Fill in the client_id and client_secret you have created in the first step.

![Integration setup_cloud](/pictures/integration_setup_cloud.png)

Depending on your installation, the modules should be added to your Home Assistant automatically within a few seconds till 10 minutes.

# Run, Play

***Run, Play*** and let us know if there are any bugs, enhancements etc via the github issues system

This plugin is a community effort and OpenMotics cannot give any warranties even though you can report any issues and we'll help as much as possible. Pull requests are always welcome.

# License

This project is licensed under the AGPLv3 License - see the [LICENSE.md](LICENSE.md) file for details

# Acknowledgments

* Special thanks to @woutercoppens for making this plugin and donating it to OpenMotics.
