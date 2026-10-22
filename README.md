# Güncel Bağlantı Rehberi

Turkish Telegram bot with exactly three persistent menu buttons: Güncel Bilgiler, Duyurular, Yardım. Includes immediate in-chat guidance, local URL structure explanation, command help, privacy information, and editable announcements. No external Python dependencies. Python 3.12 or later.

## Run

1. Create the bot with @BotFather and set a profile photo there.
2. Configure `BOT_TOKEN` as a secret in your hosting environment. Never commit it.
3. Start with `python bot.py`, or build and run the Dockerfile with BOT_TOKEN supplied at runtime.
4. Run exactly one instance as a long-running worker. This is a polling bot, not an HTTP web service; do not configure an HTTP health check. No database is required.

The bot sets its name, description, about text and command menu on startup. It refuses to start while a webhook is active; explicitly remove an old webhook only when migrating from another deployment. Stop previous polling deployments first. Invalid tokens and duplicate polling cause the process to stop. Network failures retry with backoff. SIGTERM/SIGINT stop after the current poll/request (allow at least 45 seconds of shutdown grace).

## Content

Edit `content.json` and restart/redeploy to publish content. `guide` and `announcements` are lists of plain Turkish strings, each section limited to 3400 characters. Add real dated service announcements only when you have a source and permission to publish them. No services, live status or current destination links have been invented: the initial announcements section honestly states that none are published. URL analysis never fetches submitted addresses and does not certify safety or availability.

The original requested description is configured. Before advertising, add the actual link information and access announcements it promises, or use this more accurate initial description: “Bağlantıların alan adını ve yapısını inceleyin. Türkçe bağlantı rehberini okuyun ve yayımlanan duyuruları bot içinde takip edin.”

## Suggested initial ad

Bağlantıların alan adını ve yapısını inceleyin. Güncel Bağlantı Rehberi ile bağlantı kullanımına dair Türkçe bilgileri bot içinde okuyun.

Telegram Ads approval is not guaranteed. Profile photo, actual content and advertising must match. References: https://ads.telegram.org/guidelines and https://core.telegram.org/bots/api

## Check

Run `python -m unittest -v`. After deployment test /start twice, every menu button, /help, /privacy, an ordinary HTTPS URL, a malformed URL and a non-text message. Live delivery requires your bot token and has not been verified by the offline tests.

The app stores no user database and logs no submitted links, message bodies or tokens. Telegram retains messages under its own policies. No unsolicited messaging or broadcast features are included.
