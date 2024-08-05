# WhiteBoard

### Video demo: https://youtu.be/U7KiW_G3DwA?si=iTXw8-9sUtsbreAV


### Description:

My final project for the CS50 course is a very simple social media app, that can be a bit similar to
Twitter.

It consist in creating a user, log into the platform, and then you can search for some friends and
follow them. You can also write and post any message you like, also you can see any message from your
friends in your feed, and of course you can like any message and save it in your "favorites".

You can personalize your profile, by uploading an avatar picture, you can also edit some other info of yourself
if you like, and ofcourse you can visit any othe user's profile.


## Structure:

- Home page
- User Profile page
- History page
- Favorites page
- Info page
- Login page
- Register page
- Search page
- Settings page


## Usage:

In this web-app the user can write messages with a max of 150 characters and post them into the feed that
would be the home page.

Every logged user can see every message posted by any other user they're currently following on the home page, and can interact with said messages marking/un-marking them as favorites.

Every message marked as favorite will be saved and posted in the favorite's page of the user in session. The number
of favorites will be shown in the message card. The user can then un-favorite the message if they want.

The user can see every message posted by themselves in the history page. Then they can edit or delete any of their own
messages too.

In the profile page some info of the user will be displayed, like their user name, the date they joined, their avatar picture, how many users follow them and how many they follow. Also you'll see the last message they liked, as well as the last messaged posted by them. The user in session can visit any user's profile and interact with them, liking their messages or following/unfollowing them.

In the favorites page, you'll see a list of all the messages liked by user. This page isn't accessible if the user visit other user's profile.

In the history page, you can see all messages posted by the user. The user can edit or delete any of their own messages anywhere they are shown on screen.

In the info page, you can see some extra info the user might provide, as well as a list of all users following or being followed by them.

In the search page, you can see a list of any matching existing users corresponding your prompt in the search bar.

In the setting page, the user can decide to edit some curcial info of their account, like, their username, or their password. They also can decide to delete their account for good!


### Technology used:

For front-end:

- HTML and CSS
- Bootstrap
- JavaScript


For back-end:
- Flask
- Jinja
- Python
- SQLite


Thank you very much, I'm Corina IDL and this is CS50.
