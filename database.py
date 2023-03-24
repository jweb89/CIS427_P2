import sqlite3

conn = sqlite3.connect('stocks.db', check_same_thread=False)


def init():
    conn.execute('''create table if not exists Users
            (
                user_id varchar(255) PRIMARY KEY,
                password varchar(255),
                usd_balance DOUBLE NOT NULL,
                root BOOLEAN NOT NULL
                ); ''')
    conn.execute('''create table if not exists Stocks
            (
                ID INTEGER PRIMARY KEY,
                stock_symbol varchar(4) NOT NULL,
                stock_balance DOUBLE,
                user_id varchar(255) NOT NULL,
                FOREIGN KEY (user_id) REFERENCES Users(user_id)
                ); ''')

    user = conn.execute('''SELECT * FROM Users WHERE user_id = 'root';''')

    if (user.fetchone() is None):
        conn.execute('''INSERT INTO Users (user_id, password, usd_balance, root)
        VALUES 
            ('root', 'root01', 100, 1),
            ('mary', 'mary01', 100, 0),
            ('john', 'john01', 100, 0),
            ('moe', 'moe01', 100, 0)
        ;
        ''')

    conn.commit()


def close():
    conn.close()


def getUser(user_id):
    cursor = conn.execute(
        '''SELECT * FROM Users WHERE user_id = ?''', (user_id,))
    row = cursor.fetchone()
    if row is None:
        return None
    else:
        return row


def buy_stock(stock_symbol, stock_balance, stock_price, user_id):
    # application allows 1 client currently
    # checks to make sure passed id=1
    if (getUser(user_id) == None):
        return "User"+str(user_id)+" doesn't exist"
    # Check if user has enough money
    user = conn.execute('''SELECT * FROM Users
    WHERE user_id = ?;
    ''', (user_id,)).fetchone()

    if (user[2] < stock_balance * stock_price):
        return "400 Not enough money"

    # Check if user already has stock
    stock = conn.execute('''SELECT * FROM Stocks
    WHERE stock_symbol = ? AND user_id = ?;
    ''', (stock_symbol, user_id)).fetchone()

    if (stock is not None):
        # Update stock balance
        stock = conn.execute('''UPDATE Stocks
        SET stock_balance = stock_balance + ?
        WHERE stock_symbol = ? AND user_id = ?;
        ''', (stock_balance, stock_symbol, user_id))
    else:
        # Add stock
        conn.execute('''INSERT INTO Stocks (stock_symbol, stock_balance, user_id)
        VALUES (?, ?, ?);
        ''', (stock_symbol, stock_balance, user_id))
    # Adjust balance
    user = conn.execute('''UPDATE Users
    SET usd_balance = usd_balance - ?
    WHERE user_id = ?;
    ''', (stock_balance * stock_price, user_id))
    conn.commit()

    # Fetch user and stock balance
    user = conn.execute('''SELECT * FROM Users
    WHERE user_id = ?;
    ''', (user_id,)).fetchone()
    stock = conn.execute('''SELECT * FROM Stocks
    WHERE stock_symbol = ? AND user_id = ?;
    ''', (stock_symbol, user_id)).fetchone()

    return "200 ok \nBOUGHT: New balance: " + str(stock[2]) + " " + stock[1].upper() + " USD balance: " + str(user[2])


def sell_stock(stock_symbol, stock_balance, stock_price, user_id):
    # application allows 1 client currently
    # checks to make sure passed id=1
    if (getUser(user_id) == None):
        return "User"+str(user_id)+" doesn't exist"

    # Check if user has enough stock
    stock = conn.execute('''SELECT * FROM Stocks
    WHERE stock_symbol = ? AND user_id = ?;
    ''', (stock_symbol, user_id)).fetchone()

    if (stock is None or stock[2] < stock_balance):
        return "400 Not enough stock"

    # Delete stock if balance is 0
    if (stock[2] == stock_balance):
        conn.execute('''DELETE FROM Stocks
        WHERE stock_symbol = ? AND user_id = ?;
        ''', (stock_symbol, user_id))
    else:
        # Update stock balance
        conn.execute('''UPDATE Stocks
        SET stock_balance = stock_balance - ?
        WHERE stock_symbol = ? AND user_id = ?;
        ''', (stock_balance, stock_symbol, user_id))

    # Adjust balance
    conn.execute('''UPDATE Users
    SET usd_balance = usd_balance + ?
    WHERE user_id = ?;
    ''', (stock_balance * stock_price, user_id))
    conn.commit()

    # Fetch user and stock balance
    user = conn.execute('''SELECT * FROM Users
    WHERE user_id = ?;
    ''', (user_id,)).fetchone()
    stock = conn.execute('''SELECT * FROM Stocks
    WHERE stock_symbol = ? AND user_id = ?;
    ''', (stock_symbol, user_id)).fetchone()

    stockBalance = stock[2] if stock is not None else 0

    return "200 ok \nSOLD: New balance: " + str(stockBalance) + " " + stock_symbol.upper() + " USD balance: " + str(user[2])


def login(user_id, password):
    user = conn.execute('''SELECT * FROM Users
    WHERE user_id = ? AND password = ?;
    ''', (user_id, password)).fetchone()

    if (user is None):
        return "403 Wrong UserID or Password", False, None

    return "200 ok", True, user


def list_stocks_root():
    rows = conn.execute('''SELECT * FROM Stocks;''').fetchall()

    if (rows is None or len(rows) == 0):
        return "200 ok \nNo stocks"

    stocks = "The list of records in the Stock database are:\n"
    for row in rows:
        stocks += row[1] + " " + str(row[2]) + " " + str(row[3]) + "\n"

    return "200 ok \n" + stocks.strip()


def list_stocks(user):
    rows = conn.execute('''SELECT * FROM Stocks
    WHERE user_id = ?;
    ''', (user[0],)).fetchall()

    if (rows is None or len(rows) == 0):
        return "200 ok \nNo stocks"

    stocks = f"The list of records in the Stock database for {user[0]}:\n"
    for row in rows:
        stocks += row[1] + " " + str(row[2]) + "\n"

    return "200 ok \n" + stocks.strip()


def deposit(amount, user):
    try:
        amount = float(amount)
    except ValueError:
        return "400 Invalid amount"
    conn.execute('''UPDATE Users
    SET usd_balance = usd_balance + ?
    WHERE user_id = ?;
    ''', (amount, user[0]))
    conn.commit()

    # Get new balance
    user = getUser(user[0])

    return "200 ok \nDeposited successfully. New balance $" + str(user[2])

# Lookup stock for user partial or full match on stock symbol for a given user


def lookup_stock(stock_symbol, user):
    rows = conn.execute('''SELECT * FROM Stocks
    WHERE lower(stock_symbol) LIKE ? AND user_id = ?;
    ''', (f"%{stock_symbol.lower()}%", user[0])).fetchall()

    if (rows is None or len(rows) == 0):
        return "200 ok \n404 Your search did not match any records"

    stocks = "Found " + str(len(rows)) + \
        (" match\n" if len(rows) == 1 else " matches\n")
    for row in rows:
        stocks += row[1] + " " + str(row[2]) + "\n"

    return "200 ok \n" + stocks.strip()


def get_balance(user_id):
    user = conn.execute('''SELECT user_id, usd_balance FROM Users
    WHERE user_id = ?;
    ''', (user_id,)).fetchone()
    return "200 ok \nBalance for user " + user[0] + ": $" + str(user[1])
