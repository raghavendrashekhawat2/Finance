import os
import datetime

from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")

# Make sure API key is set
if not os.environ.get("API_KEY"):
    raise RuntimeError("API_KEY not set")


@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""
    quantity = 0
    cash =db.execute("SELECT cash FROM users where id = :id",id = session["user_id"])
    portf = db.execute("SELECT c_name,symbol,quantity FROM transactions WHERE user_id = :user_id ",user_id = session["user_id"])
    l = len(portf)
    sum = 0


    for stock in range (l) :
        details =  lookup(portf[stock]["symbol"])
        print(lookup(portf[stock]["symbol"]))
        portf[stock]['price'] = details["price"]

     #    sum += portf[stock]['total']
    cash = cash[0]["cash"]
    return render_template("index.html",portf=portf,cash=cash)


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""
    quantity = 0
    if request.method == "POST" :
        n = int(request.form.get("shares"))
        sym = lookup(request.form.get("symbol"))

        if sym == None :
            return apology("Wrong symbol entered",400)
        elif n <= 0 :
            return apology("Enter a positive number",400)



        # LOGIC
        price = sym["price"]
        c =db.execute("SELECT cash FROM users WHERE id = :id ",id = session["user_id"])
        cash = (c[0]["cash"])

        if price*n > cash :
            return apology("Insufficient cash",400)
        p_s = 'p'
        d = db.execute("SELECT * FROM transactions WHERE user_id = :user_id AND symbol = :symbol", user_id = session["user_id"], symbol = request.form.get("symbol"))
        flag = 0
        print(len(d))

        if d == None or len(d) == 0 :
            flag = 1
        # CREATE a new table and store all details of the trasaction and insert new rows each time the user buys stock
        a = db.execute("INSERT INTO history (userid,c_name,symbol,price,quantity,datetime,p_s) VALUES (:userid,:c_name,:symbol,:price,:quantity,:datetime,'purchased')"
            ,userid = session["user_id"],c_name = sym["name"],symbol = sym["symbol"],price = sym["price"],quantity = request.form.get("shares"),datetime = datetime.datetime.now())
        if flag == 1 :
            a = db.execute("INSERT INTO transactions (user_id,c_name,symbol,price,quantity,date_time) VALUES (:user_id,:c_name,:symbol,:price,:quantity,:date_time)"
               ,user_id = session["user_id"],c_name = sym["name"],symbol = sym["symbol"],price = sym["price"],quantity = request.form.get("shares"),date_time = datetime.datetime.now())
        else :
            quantity = d[0]['quantity']
            quantity += int(request.form.get("shares"))
            a = db.execute("UPDATE transactions SET quantity = :quantity WHERE user_id = :user_id AND symbol = :symbol",quantity = quantity,user_id = session["user_id"],symbol = request.form.get("symbol"))
        quantity = 0
        cash -= price*n
        usid = db.execute("UPDATE users SET cash = :cash WHERE id = :id",cash = cash,id =session["user_id"])
        flash("Bought")
        del d[:]
        return redirect("/")





    else :
        return render_template("buy.html")


@app.route("/check", methods=["GET"])
def check():


    """Return true if username available, else false, in JSON format"""
    return jsonify("TODO")


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""
    info = db.execute("SELECT * FROM history WHERE userid = :userid ",userid = session["user_id"])
    for stock in range (len(info)) :
        info[stock]['price'] = lookup(info[stock]["symbol"])

    return render_template("history.html",info = info)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""
    if request.method == "POST" :
        res = lookup(request.form.get("symbol"))
        if not res :
            return apology("Enter a symbol",400)
        return render_template("quote2.html",res = res)



    else :
        return render_template("quote1.html")
        print ("YES")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    session.clear()
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 400)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 400)

        # Ensure password and confirmation match
        elif not request.form.get("password") == request.form.get("confirmation"):
            return apology("passwords do not match", 400)
        rows = db.execute("SELECT  * FROM users WHERE username = :username",username = request.form.get("username"))
        print (rows)

        if not len(rows) == 0:
            return apology("username taken", 400)

        # hash the password and insert a new user in the database
        hash = generate_password_hash(request.form.get("password"))
        result = db.execute("INSERT INTO users (username, hash) VALUES(:username, :hash)", username=request.form.get("username"), hash=hash)




        # Remember which user has logged in
        session["user_id"] = result
        print(result)

        # Display a flash message
        flash("Registered!")

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")

@app.route("/addcash", methods=["GET" , "POST"])
@login_required
def addcash():
    """Add Cash """
    if request.method == "POST" :
        if int(request.form.get("amt")) <= 0 :
            return apology("Enter a number greater than 0",400)
        c = db.execute("SELECT cash FROM users WHERE id = :id",id = session["user_id"])
        c = c[0]["cash"]
        cash = int(request.form.get("amt")) + c
        a = db.execute("UPDATE users SET cash = :cash WHERE id = :id ",cash = cash ,id = session["user_id"])

        return redirect("/")

    else :
        return render_template("addcash.html")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""
    quantity = 0
    if request.method == "POST" :
        if not request.form.get("symbol") :
            return apology("You must select a stock",400)
        if not request.form.get("shares") :
            return apology("You must enter the quantity",400)
        if int(request.form.get("shares")) < 1 :
            return apology("Enter a number greater than one",400)
        info = db.execute("SELECT * FROM transactions WHERE user_id = :user_id AND symbol = :symbol",user_id = session["user_id"],symbol= request.form.get("symbol"))
        quantity = info[0]["quantity"]
        print(f"Quantity is : {quantity}")
        if int(request.form.get("shares")) > int(info[0]["quantity"]) :
            return apology("You dont have entered amount of shares",400)
        # Calculating final cash after selling stock
        cash = db.execute("SELECT cash FROM users WHERE id = :id",id = session["user_id"])
        cash = cash[0]["cash"]
        det = lookup(info[0]["symbol"])
        price = det["price"]
        cash += (info[0]["quantity"] * price)
        print(cash)
        symbol = request.form.get("symbol")


        a = db.execute("INSERT INTO history (userid,c_name,symbol,price,quantity,datetime,p_s) VALUES (:userid,:c_name,:symbol,:price,:quantity,:datetime,'sold')"
            ,userid = session["user_id"],c_name = info[0]["c_name"],symbol = det["symbol"],price = det["price"],quantity = request.form.get("shares"),datetime = datetime.datetime.now())
        # Update quantity
        quantity = quantity - int(request.form.get("shares"))
        print(f"Quantity is after subtractiong : {quantity}")
        if quantity > 0 :
            b = db.execute("UPDATE  transactions SET quantity = :quantity WHERE user_id = :user_id AND symbol = :symbol",quantity = quantity,user_id = session["user_id"],symbol = symbol)
        else :
            b = db.execute("DELETE FROM transactions WHERE user_id = :user_id AND symbol = :symbol",user_id = session["user_id"],symbol = det["symbol"])

        id = db.execute("UPDATE users SET cash = :cash WHERE id = :id",cash = cash ,id = session["user_id"])
        flash
        quantity = 0
        del info[:]


        return redirect("/")




    else:
        portf = db.execute("SELECT symbol from transactions WHERE user_id = :user_id",user_id = session["user_id"])
        return render_template("sell.html",portf = portf )


def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
