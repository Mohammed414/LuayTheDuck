import telepot
from telepot.loop import MessageLoop
from telepot.namedtuple import InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, \
    InlineKeyboardMarkup
import mysql.connector
from datetime import datetime

# the id of the owner that notifications will be sends to
owner_id = 40382341


# returns a connection to the server
def connect():
    db = mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="luay's_users"
    )
    return db


# checks whether the user is a new or and old customer. (all users ids are stored in database)
def handle_new_users(db, user_id, name):
    users_id = []
    mycursor = db.cursor()
    mycursor.execute("SELECT user_id FROM users")
    rows = mycursor.fetchall()
    for row in rows:
        users_id.append(row[0])
    if str(user_id) not in users_id:
        bot.sendMessage(user_id, "Hey!")
        # date and time
        now = datetime.now()
        date = now.strftime("%Y-%m-%d %H:%M:%S")
        sql = "INSERT INTO users VALUES (%s, %s, %s, %s)"
        mycursor.execute(sql, (None, user_id, name, date))
        db.commit()
    else:
        bot.sendMessage(user_id, f"Welcome back! {name}!")


# an important function that deals with sessions of orders.
def handle_session(chat_id, sessiondb, command, session_id, message_id):
    mycursor = sessiondb.cursor()
    mycursor.execute("SELECT state, cart_id FROM sessions WHERE chat_id = " + str(chat_id))
    row = mycursor.fetchall()
    if not row:
        # calculate cart_id (message will be edited
        cart_id = message_id + items(chat_id)
        print("cart_id", cart_id)
        mycursor.execute("INSERT INTO sessions VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                         (None, chat_id, 1, "name", "000", "123 Fake street", cart_id, "[]"))
        sessiondb.commit()
        bot.sendMessage(chat_id, "Ok, let's start! What do you want to buy?")

    else:
        state = row[0][0]
        if state == 1:
            if command == "done":
                # continue
                mycursor.execute("UPDATE sessions SET state = 2 WHERE chat_id = " + str(chat_id))
                sessiondb.commit()
                bot.sendMessage(chat_id, "Ok, let's continue! What's your name?")

                # delete all session order and move them to the other table
                sql = "DELETE FROM session_order WHERE session_id = " + str(session_id)
                mycursor.execute(sql)
                sessiondb.commit()

            elif not isinstance(command, list):
                bot.sendMessage(chat_id, "invalid command. Pick a pizza first. When done, press the done button.")
                pass
            else:
                operation = {'do': command[0], 'name': command[1]}
                if checkItem(operation['name'], session_id, sessiondb):
                    if operation['do'] == "+1":
                        mycursor.execute("UPDATE session_order SET quantity = (quantity + 1) WHERE session_id = " + str(
                            session_id) + " AND name = '" + operation['name'] + "'")
                        sessiondb.commit()
                    else:
                        # check if <= 1. if it's 1 or less then just delete it entirely
                        mycursor.execute("SELECT quantity FROM session_order WHERE session_id = " + str(
                            session_id) + " AND name = '" + operation['name'] + "'")
                        quantity = mycursor.fetchall()[0][0]
                        if quantity <= 1:
                            # delete entirely
                            mycursor.execute(
                                "DELETE FROM session_order WHERE session_id = " + str(session_id) + " AND name = '" +
                                operation['name'] + "'")
                            sessiondb.commit()
                        else:
                            # delete ONLY ONE if  > 1
                            mycursor.execute(
                                "UPDATE session_order SET quantity = (quantity - 1) WHERE session_id = " + str(
                                    session_id) + " AND name = '" + operation['name'] + "'")
                            sessiondb.commit()
                else:
                    if operation['do'] == "+1":
                        # insert a new session item
                        mycursor.execute("INSERT INTO session_order VALUES (%s, %s, %s, %s)",
                                         (None, session_id, operation['name'], 1))
                        sessiondb.commit()
                    else:
                        bot.sendMessage(chat_id, "Pick a thing first")
                # update cart message
                cart = getCart(chat_id, sessiondb, session_id)
                message_id = cart[0]
                orders = cart[1]
                orderList = "Cart: \n"
                for order in orders:
                    # list or orders with the quantity
                    orderList += f"{order[0]} X {order[1]}\n"
                bot.editMessageText((chat_id, message_id), text=orderList)
                mycursor.execute("UPDATE sessions SET order_list = '" + orderList + "' WHERE chat_id = " + str(chat_id))
                sessiondb.commit()
                # print(order)
        if state == 2:
            # bot.sendMessage(chat_id, f"Ok let's continue. You're on state {state}")
            mycursor.execute("UPDATE sessions SET full_name = '" + command + "' WHERE chat_id = " + str(chat_id))
            sessiondb.commit()
            mycursor.execute("UPDATE sessions SET state = 3 WHERE chat_id = " + str(chat_id))
            sessiondb.commit()
            bot.sendMessage(chat_id, "Please provide a phone number.")
        if state == 3:
            mycursor.execute("UPDATE sessions SET phone_number = '" + command + "' WHERE chat_id = " + str(chat_id))
            sessiondb.commit()
            mycursor.execute("UPDATE sessions SET state = 4 WHERE chat_id = " + str(chat_id))
            sessiondb.commit()
            # bot.sendMessage(chat_id, f"You're on state {state}")
            keyboard = [[KeyboardButton(text="Send GPS coordinates", request_location=True)]]
            markup = ReplyKeyboardMarkup(keyboard=keyboard)
            bot.sendMessage(chat_id, "Now send us your address!")
            bot.sendMessage(chat_id, "Write down the address or just send us your gps coordinates.",
                            reply_markup=markup)
        if state == 4:
            # remove GPS keyboard
            markup = ReplyKeyboardRemove()
            bot.sendMessage(chat_id, "Done!", reply_markup=markup)
            mycursor.execute("UPDATE sessions SET address = '" + command + "' WHERE chat_id = " + str(chat_id))
            sessiondb.commit()
            submitSession(chat_id, sessiondb)
            KillSession(chat_id, sessiondb)


# gets the content of the cart
def getCart(chat_id, mydb, session_id):
    mycursor = mydb.cursor()
    mycursor.execute("SELECT cart_id FROM sessions WHERE chat_id = " + str(chat_id))
    rows1 = mycursor.fetchall()
    mycursor.execute("SELECT name, quantity FROM session_order WHERE session_id = " + str(session_id))
    rows2 = mycursor.fetchall()
    # returns cart message id & the content
    return [rows1[0][0], rows2]


# check if there are any already
def checkItem(name, session_id, mydb):
    mycursor = mydb.cursor()
    mycursor.execute("SELECT * FROM session_order WHERE session_id = " + str(session_id) + " AND name = '" + name + "'")
    rows = mycursor.fetchall()
    print(rows)
    if not rows:
        return False
    else:
        return True


# submits the session as an order
def submitSession(chat_id, mydb):
    mycursor = mydb.cursor()
    mycursor.execute(
        "SELECT full_name, phone_number, address, order_list FROM sessions WHERE chat_id = " + str(chat_id))
    row = mycursor.fetchall()[0]
    # date
    now = datetime.now()
    date = now.strftime("%Y-%m-%d %H:%M:%S")
    fullRow = (None, row[0], row[1], row[2], date, row[3])
    print(fullRow)
    sql = "INSERT INTO orders VALUES (%s, %s, %s, %s, %s, %s)"
    mycursor.execute(sql, fullRow)
    mydb.commit()
    notify(owner_id, fullRow)


# ends a session
def KillSession(chat_id, mydb):
    mycursor = mydb.cursor()
    sql = "DELETE FROM sessions WHERE chat_id = " + str(chat_id)
    mycursor.execute(sql)
    mydb.commit()


# sends a notification of the order to the owner
def notify(owener, order):
    message = f"New order from {order[1]}\n phone number: {order[2]}\n adress: {order[3]}\n date: {order[4]}\n Order:\n {order[5][7:]} "
    bot.sendMessage(owener, message)


def checkSession(chat_id, db):
    mycursor = db.cursor()
    mycursor.execute("SELECT state FROM sessions WHERE chat_id = " + str(chat_id))
    row = mycursor.fetchall()
    if not row:
        return False
    else:
        return True


def getSessionId(chat_id, db):
    mycursor = db.cursor()
    mycursor.execute("SELECT id FROM sessions WHERE chat_id = " + str(chat_id))
    row = mycursor.fetchall()
    if not row:
        return None
    else:
        return row[0][0]


def items(chat_id):
    mydb = connect()
    mycursor = mydb.cursor()
    mycursor.execute("SELECT name, category, price, description, image, id FROM pizzas_items")
    rows = mycursor.fetchall()
    n = 0
    for row in rows:
        # TODO
        caption = f"{row[0]}\nCategory: {row[1]}\n Price: {row[2]}\n{row[3]}"
        path = "static/" + row[4]
        keyboard = [[InlineKeyboardButton(text="ADD", callback_data=f"+1, {row[0]}"),
                     InlineKeyboardButton(text="REMOVE", callback_data=f"-1, {row[0]}")]]
        markup = InlineKeyboardMarkup(inline_keyboard=keyboard)

        bot.sendPhoto(chat_id, open(path, 'rb'), caption=caption, reply_markup=markup)
        n += 1
    keyboard = [[InlineKeyboardButton(text="Done!", callback_data="done")]]
    markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
    bot.sendMessage(chat_id, "When you finish just click done!", reply_markup=markup)
    bot.sendMessage(chat_id, "Your Cart 🛒: \nempty--")
    return n + 2


def handle(msg):
    print(msg)
    if "message_id" in dict.keys(msg):
        message_id = msg['message_id']
    else:
        message_id = 0
    mydb = connect()
    if "chat" in dict.keys(msg):
        chat_id = msg['chat']['id']
    else:
        chat_id = msg['from']['id']
    if "location" in dict.keys(msg):
        coord = msg['location']
        command = f"https://www.google.com/maps/dir//{coord['latitude']},{coord['longitude']}"
    if "text" in dict.keys(msg):
        command = msg['text']

    elif "data" in dict.keys(msg):
        command = (msg['data']).split(",")
        print(command)
        if len(command) < 2:
            command = "done"


    if command == "/buy" or checkSession(chat_id, mydb):
        session_id = getSessionId(chat_id, mydb)
        handle_session(chat_id, mydb, command, session_id, message_id)

    first_name = msg['from']['first_name']
    if command == "/start":
        handle_new_users(mydb, chat_id, first_name)

    if command == "/menu":
        bot.sendPhoto(chat_id, open("static/other/oxq-pizza-menu-template-edit-online.jpg", 'rb'))
    if command == "/all":
        mydb = connect()
        mycursor = mydb.cursor()
        mycursor.execute("SELECT name, category, price, description, image, id FROM pizzas_items")
        rows = mycursor.fetchall()
        for row in rows:
            # TODO
            caption = f"{row[0]}\nCategory: {row[1]}\n Price: {row[2]}\n{row[3]}"
            path = "static/" + row[4]
            keyboard = [[InlineKeyboardButton(text="➕", callback_data=f"+1, {row[0]}"),
                         InlineKeyboardButton(text="➖", callback_data=f"-1, {row[0]}")]]
            markup = InlineKeyboardMarkup(inline_keyboard=keyboard)

            bot.sendPhoto(chat_id, open(path, 'rb'), caption=caption, reply_markup=markup)
        keyboard = [[InlineKeyboardButton(text="Done!", callback_data="done")]]
        markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
        bot.sendMessage(chat_id, "When you're finished just click done!", reply_markup=markup)


print("up and running...")
Token = "1973983480:AAFM_W9dxdFzigiv5RD_ffBQmYKClomQrU0"
bot = telepot.Bot(Token)
MessageLoop(bot, handle).run_forever()
