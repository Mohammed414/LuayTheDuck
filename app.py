import os
import mysql.connector
from flask import Flask, render_template, request, url_for, flash, redirect
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = 'static\images'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True
# images config
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "GET":
        mydb = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database="luay's_users"
        )

        mycursor = mydb.cursor()
        mycursor.execute("SELECT * FROM orders")
        rows = mycursor.fetchall()
        return render_template("index.html", rows=rows[::-1], x=url_for("index"))


@app.route("/upload", methods=["GET", "POST"])
def upload():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            return redirect("/")
        file = request.files['file']
        # If the user does not select a file, the browser submits an
        # empty file without a filename.
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

            # import the item in database
            item_name = request.form['item_name']
            item_category = request.form['item_category']
            item_description = request.form['item_description']
            item_price = request.form['item_price']
            item_image = f"images/{filename}"

            querytuple = (None, item_category, item_name, item_description, item_price, True, item_image)
            mydb = mysql.connector.connect(
                host="localhost",
                user="root",
                password="",
                database="luay's_users"
            )
            mycursor = mydb.cursor()
            print(querytuple)
            mycursor.execute("INSERT INTO pizzas_items VALUES (%s, %s, %s, %s, %s, %s, %s)", querytuple)
            mydb.commit()

    return render_template("upload.html")


@app.route("/items", methods=["GET", "POST"])
def items():
    mydb = mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="luay's_users"
    )
    mycursor = mydb.cursor()
    mycursor.execute("SELECT * FROM pizzas_items")
    rows = mycursor.fetchall()
    print(rows)
    return render_template("items.html", rows=rows)
