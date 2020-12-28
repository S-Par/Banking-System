# (A Simple) Banking System
This is a simple banking system that allows you to create an account (auto-generating a unique 16-digit credit card number and 4-digit PIN), login to accounts, add money, and transfer money.  
  
This application utilizes sqlite3 to allow data to persist between runs. This will cause the generation of a 'card.s3db' file that will be *ignored* by Git!  

## Quick Start
Cloning the repository via the command line:

```console
$ git clone https://github.com/S-Par/Banking-System.git
$ cd Banking-System/
$ python3 banking.py
```

## Credit Card Number generation:
All credit cards begin with the sequence "400000". The next 10 digits of the credit card number are unique to each user. The last digit is the checksum of the credit card number—calculated according to the [Luhn Algorithm](https://en.wikipedia.org/wiki/Luhn_algorithm).
