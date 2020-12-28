import random
import sqlite3


# Updates the balance of one account when given the relevant params
def update_db_balance(account, connection_obj, card):
    # Update the database
    card.execute(f'UPDATE card SET balance = {account.balance} '
                 f'WHERE pin = {account.pin};')
    connection_obj.commit()


class Account:
    accounts = dict()

    def __init__(self, card_num, pin):
        self.pin = pin
        self.card_num = card_num
        self.balance = 0

    def add_income(self, amount, connection_obj, card):
        self.balance += amount
        update_db_balance(self, connection_obj, card)

    def transfer_money(self, connection_obj, card):
        print("\nTransfer")
        card_num = input("Enter card number:\n>")
        if card_num == self.card_num:
            print("You can't transfer money to the same account!\n")
        elif generate_checksum(card_num[:-1]) != card_num[-1]:
            print("Probably you made a mistake in the card number. Please try again!\n")
        elif card_num not in Account.accounts.values():
            print("Such a card does not exist.\n")
        else:
            amount = int(input("Enter how much money you want to transfer:\n>"))
            if amount > self.balance:
                print("Not enough money!\n")
            else:
                # Transfer money to receiver as all conditions are valid
                # Get the exisitng balance and pin of the receiver
                # Then initialize receiver obj
                card.execute(f'SELECT pin, balance FROM card WHERE number = {card_num};')
                connection_obj.commit()
                receiver_pin, receiver_balance = card.fetchone()
                receiver = Account(card_num, receiver_pin)
                receiver.balance = receiver_balance
                # Reflect the changes in both balances due to the transfer
                self.balance -= amount
                update_db_balance(self, connection_obj, card)
                receiver.balance += amount
                update_db_balance(receiver, connection_obj, card)
                print("Success!\n")

    def close_account(self, connection_obj, card):
        # Remove the accounts data value of pin:card_num
        del Account.accounts[self.pin]
        # Remove the field from the DB
        card.execute(f'DELETE FROM card WHERE number = {self.card_num};')
        connection_obj.commit()


# Creates a unique pin between 0000 and 9999 (inclusive)
def generate_unique_pin():
    new_pin = random.randint(0, 9999)
    str_pin = str(new_pin)
    # Add 0s to the starting to make the pin 4-digit:
    str_pin = ('0' * (4 - len(str_pin))) + str_pin
    if str_pin not in Account.accounts.keys():
        return str_pin
    return generate_unique_pin()


# Creates the appropriate checksum for card num according to Luhn's algorithm
def generate_checksum(prior_card_num):
    digit_sum = 0
    for i in range(len(prior_card_num)):
        # Odd digits for Luhn's algo are at even indices since lists are 0-indexed
        if i % 2 == 0:
            digit = int(prior_card_num[i]) * 2
            if digit > 9:
                digit -= 9
            digit_sum += digit
        else:
            digit = int(prior_card_num[i])
            digit_sum += digit
    if digit_sum % 10 == 0:
        return '0'
    return str(10 - (digit_sum % 10))


# Creates a unique card num starting with 400000 and ending with the checksum
def generate_unique_card_num():
    new_account_num = random.randint(0, 999999999)
    str_account_num = ('0' * (9 - len(str(new_account_num)))) + str(new_account_num)
    card_num_without_checksum = '400000' + str_account_num
    card_num = card_num_without_checksum + generate_checksum(card_num_without_checksum)
    if card_num not in Account.accounts.values():
        return card_num
    return generate_unique_card_num()


# Generates a unique card num and pin as well as initializing an Account obj
def create_account():
    # Create the unique pin and corresponding card num
    pin = generate_unique_pin()
    card_num = generate_unique_card_num()
    Account.accounts[pin] = card_num

    print("\nYour card has been created")
    print("Your card number:", card_num, sep="\n")
    print("Your card PIN:", pin, sep="\n")
    print()
    return card_num, pin


# Checks if the user has entered appropriate credentials to login
def login(card_num, pin):
    if pin not in Account.accounts.keys() or Account.accounts[pin] != card_num:
        print("Wrong card number or PIN!\n")
        return False
    else:
        print("You have successfully logged in!\n")
        return True


# Runs the secondary menu allowing a logged in user to do tasks
def login_menu(account, connection_obj, card):
    print("1. Balance", "2. Add income", "3. Do transfer", "4. Close account", 
          "5. Log out", "0. Exit", sep="\n")
    option = int(input(">"))
    if option == 1:
        print("\nBalance:", account.balance, "\n")
    elif option == 2:
        amount = int(input("Enter income:\n>"))
        account.add_income(amount, connection_obj, card)
        print("Income was added!\n")
    elif option == 3:
        account.transfer_money(connection_obj, card)
    elif option == 4:
        account.close_account(connection_obj, card)
        print("\nThe account has been closed!\n")
        return False
    elif option == 5:
        return False
    elif option == 0:
        print('\nBye!')
        connection_obj.close()
        exit()
    return True


# Initializes the database and Account.accounts dict:
def database_init(connection_obj, card):
    # Create the card table if it's not already created
    try:
        card.execute('CREATE TABLE card(id INTEGER, '
                     'number TEXT, '
                     'pin TEXT, balance INTEGER DEFAULT 0);')
        connection_obj.commit()
    except:
        # We reach here only if the table already exists
        # We need to check if the existing table has our requisite columns
        # If not, we delete the table and start again
        card.execute('SELECT id FROM card;')
        connection_obj.commit()
        if card.fetchone() is None:
            card.execute('DROP TABLE card;')
            connection_obj.commit()
            database_init(connection_obj, card)

    # Fetch all the existing records and update accounts
    card.execute('SELECT pin, number FROM card;')
    connection_obj.commit()
    for record in card.fetchall():
        # record is a tuple of the form (pin, card_num)
        Account.accounts[record[0]] = record[1]


def main():
    # Create a Connection to the card database
    connection_obj = sqlite3.connect('./card.s3db')

    # Create a Cursor obj to perform queries on the database
    card = connection_obj.cursor()

    # Initialize based on database:
    database_init(connection_obj, card)

    while True:
        print("1. Create an account", "2. Log into account", "0. Exit", sep="\n")
        option = int(input(">"))

        if option == 1:
            card_num, pin = create_account()
            # Check how many records are in the table and set id accordingly:
            card.execute('SELECT * FROM card;')
            connection_obj.commit()
            user_id = len(card.fetchall()) + 1
            # Add record to the database:
            card.execute('INSERT INTO card(id, number, pin, balance) '
                         f'VALUES ({user_id}, {card_num}, {pin}, 0);')
            connection_obj.commit()
        elif option == 2:
            card_num = input("\nEnter your card number:\n>")
            pin = input("Enter your PIN:\n>")
            if login(card_num, pin):
                # Create Account object and initialize with saved DB values:
                account = Account(card_num, pin)
                card.execute(f'SELECT balance FROM card WHERE pin = {pin};')
                connection_obj.commit()
                account.balance = card.fetchone()[0]

                while login_menu(account, connection_obj, card):
                    pass
        elif option == 0:
            print("\nBye!")
            connection_obj.close()
            break

if __name__ == '__main__':
    main()

