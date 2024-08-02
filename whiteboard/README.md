# Social Media App

My final project for the CS50 course is a very simple social media app, that can be a bit similar to
Twitter.

It consist in creating a user, log into the platform, and then you can search for some friends and
follow them. You can also write and post any message you like, also you can see any message from your
friends in your feed, and of course you can like any message and save it in your "favorites".

You can personalize your profile uploading an avatar picture, you can also edit some other info of yourself
if you like, and ofcourse you can visit any othe user's profile.


## Structure:

- Home page
- User Profile page
- History page
- Favorites page
- Info page
- Login page
- Register page
- Settings page


## Uses:

In this web-app the user can write messages with a max of 150 characters and post them into the feed that
would be the home page.

Every logged user can see every message posted by any other user in the feed page, and can interact with
said messages marking them as favorites.

Every message marked as favorite will be saved and posted in the favorite's page of each user. The number
of favorites will be shown in the message card. The user can then unfavorite the message if they want.

The user can see every message posted by them in the history page. Then they can edit or delete any of their own
messages.

In the profile page some info of the user will be displayed, like their user name, date they joined, how many
messages have beem posted by them, how many favorites, also the last messaged posted by them as well as the
last message favorited by them.


### Technology used:

For front-end:

- HTML and CSS
- Bootstrap
- JavaScript


For back-end:
- Flask
- Jinja templates
- Python