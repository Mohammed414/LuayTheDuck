# LuayTheDuck

#### Video Demo: https://youtu.be/PbqDcbzXVzM

#### Description:

"Luay's Pizzas Shop" bot is a Telegram bot used to order pizzas. The orders are sent and organized in a database.

I used HTML, CSS, JS, and bootstrap in the frontend. Python and Flask in the backend. For the Telegram bot API, I used the library telepot.

The program is divided mainly into two sections: app.py: the Flask application that controls the website, also divided into: a) Index.html (Main website with orders organized) b) upload.html (Upload items) c) items (see the uploaded items) And for bot.py: The telegram file that runs by just typing the telegram API key and everything else is automated For the database MySql is used and managed with PHPmyadmin (SQL file for the database and the tables is included) the library mysql.connector is used to make dealing with databases easier.

the database is divided into secitons: users pizzas etc. but the most important one is sessions. it uses stages to complete the order because telegram doesn't make it easy doing it so i created my own system.

bootstrap is used to make things more responisve and prettier

telepot library makes things easier to work with the telegram api and i used this library because it's simplier than the others.
