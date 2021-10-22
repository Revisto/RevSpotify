# RevSpotify
## _A Telegram Bot that can download music from Spotify_

RevSpotify is a fast, useful telegram bot to have Spotify music on Telegram.

![](https://cdn.dribbble.com/users/460659/screenshots/4837675/media/298bfc63139e23c19a9524c2510a2504.jpg)

## ✨ Features ( till now )

- Download tracks from Spotify
- Download album from Spotify
- Download playlist from Spotify
- Download artist's top tracks from Spotify

## ⚙️ Installation

RevSpotify only and only requires [Docker](https://www.docker.com/) to run.

Install Docker and start the bot, docker takes care of other dependencies.

```sh
apt install docker-ce
```

Now clone the repo:
```sh
git clone https://github.com/revisto/RevSpotify
cd RevSpotify
```

Let's take care of .env files...

```sh
cp revspotify/.env_sample revspotify/.env
```
.env file contains your telegram bot token. fill it like this:
```
token=<TELEGRAM_ACCESS_TOKEN>
```

## Docker

Make sure that you have done all installation steps and made .env files.
then, build it and run it.
```sh
docker build -t revspotify .
docker run -d revspotify
```

## 🤝 Contributing

Contributions, issues and feature requests are welcome.<br />
Feel free to check [issues page](https://github.com/revisto/RevSpotify/issues) if you want to contribute.<br /><br />


## Show your support

Please ⭐️ this repository if this project helped you!


## 📝 License

GNUv2

**Free Software, Hell Yeah!**