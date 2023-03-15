import sqlite3

conn = sqlite3.connect('stocks.db')


def init():
    conn.execute('''create table if not exists Users
            (
                ID INTEGER PRIMARY KEY,
                first_name varchar(255),
                last_name varchar(255),
                user_name varchar(255) NOT NULL,
                password varchar(255),
                usd_balance DOUBLE NOT NULL
                ); ''')
    conn.execute('''create table if not exists Stocks
            (
                ID INTEGER PRIMARY KEY,
                stock_symbol varchar(4) NOT NULL,
                stock_balance DOUBLE,
                user_id int,
                FOREIGN KEY (user_id) REFERENCES Users(ID)
                ); ''')

    user = conn.execute('''SELECT * FROM Users WHERE ID = 1;''')

    if (user.fetchone() is None):
        conn.execute('''INSERT INTO Users (ID, first_name, last_name, user_name, password, usd_balance)
        VALUES (1, 'John', 'Doe', 'johndoe', 'password', 100);
        ''')

    conn.commit()


def close():
    conn.close()


def getUser(user_id):
    cursor = conn.execute('''SELECT * FROM Users WHERE ID = ?''', (user_id,))
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
    WHERE ID = ?;
    ''', (user_id,)).fetchone()

    if (user[5] < stock_balance * stock_price):
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
    WHERE ID = ?;
    ''', (stock_balance * stock_price, user_id))
    conn.commit()

    # Fetch user and stock balance
    user = conn.execute('''SELECT * FROM Users
    WHERE ID = ?;
    ''', (user_id,)).fetchone()
    stock = conn.execute('''SELECT * FROM Stocks
    WHERE stock_symbol = ? AND user_id = ?;
    ''', (stock_symbol, user_id)).fetchone()

    return "200 ok \nBOUGHT: New balance: " + str(stock[2]) + " " + stock[1].upper() + " USD balance: " + str(user[5])


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
    WHERE ID = ?;
    ''', (stock_balance * stock_price, user_id))
    conn.commit()

    # Fetch user and stock balance
    user = conn.execute('''SELECT * FROM Users
    WHERE ID = ?;
    ''', (user_id,)).fetchone()
    stock = conn.execute('''SELECT * FROM Stocks
    WHERE stock_symbol = ? AND user_id = ?;
    ''', (stock_symbol, user_id)).fetchone()

    stockBalance = stock[2] if stock is not None else 0

    return "200 ok \nSOLD: New balance: " + str(stockBalance) + " " + stock_symbol.upper() + " USD balance: " + str(user[5])


def list_stocks(user_id):
    rows = conn.execute('''SELECT * FROM Stocks
    WHERE user_id = ?;
    ''', (user_id,)).fetchall()

    if (rows is None or len(rows) == 0):
        return "200 ok \nNo stocks"

    stocks = ""
    for row in rows:
        stocks += row[1] + " " + str(row[2]) + " " + str(row[3]) + "\n"

    return "200 ok \n" + stocks.strip()


def get_balance(user_id):
    user = conn.execute('''SELECT usd_balance, first_name, last_name FROM Users
    WHERE ID = ?;
    ''', (user_id,)).fetchone()
    return "200 ok \nBalance for user " + user[1] + " " + user[2] + ": $" + str(user[0])
