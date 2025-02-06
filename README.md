# TwitchChatTranslator
Translator for twitch chats. Customizable with different languages and a simple GUI to indicate translated messages and non-translated messages.

To run the application download the executable directory and run twitchTranslator.exe. This will open the main menu where you will need to enter all configuration into the settings. Once this is completed clicking start will require authorization on twitch before it translates any and all messages in the chat from the selected channel.

Use of this bot requires creating a twitch bot client for a client ID and client secret. All other configuration is stored in the configuration file accessible through the main menu.

For setup on twitch side visit https://dev.twitch.tv/console and follow the steps below.
Click on Register Your Application.
Enter a name for the application.
Enter your redirect URL as the same url you use in configuration. This needs to be formatted with a open port. If unsure then use http://localhost:8080/.
Enter any category
Keep Client Type on Confidential
Complete the captcha and click Create
Copy the client_id and client_secret and enter them in their respective positions in the configuration file.