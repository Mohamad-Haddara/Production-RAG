"""
Encapsulation & Abstraction
Hide the implementation details from other prgrammers, show the interface

    - Keep the internal state private
    - Expose behavior, not data
    - Use properties/getters for controlled access
    - Abstract away thhe complexity

Ask myself: If I change this internal implementation, will client code break?


Problem without encapsulation and absraction:
1) No validation or business rules enforced
2) Internal state can be corrupted
3) Can't change implementation without breaking clients
4) No audit trail or control

Goal: When create a class, we should protect it 
"""

# Bad Encapsulation - everything is exposed andtoo flexible

class BankAccount:
    # Everything is public - no protection!

    def __init__(self, owner, balance):
        self.owner = owner
        self.balance = balance # Direct access allowed!
        self.transctions = []   # Can be manipulated directly



# Good Encapsulation and Abstraction

from typing import List, Dict, Optional
from datetime import datetime


class Transaction:
    # Encapsulate transaction details

    def __init__(self, amount: float, transaction_type: str, description: str):
        
        self._amount = amount
        self._type = transaction_type
        self._timestamp = datetime.now()
        self._description = description

class BankAccount:
    """
    Encapsulate bank account with controlled acess

    - We have privatge attribute in Python --> _balance --> internal to the class ans should not modify it from outside
    """

    def __init__(self, owner: str, initial_balance: float = 0):


        # Private attribute that are used internally
        self._owner = owner
        self._balannce = initial_balance # Private attribute
        self._transactions: List[Transaction] = [] # Private attribute

        if initial_balance > 0:
            self._add_transaction(initial_balance, "DEPOSIT", "Initial deposit")

    # Public interface(methods) - abstraction of account opeartions
    def deposit(self, amount: float, description: str = "Deposit"):
        # Deposit money - with validation
        if amount <= 0:
            raise ValueError("Deposit amount must be positive")

        # Modify internal state
        self._balance += amount
        self._add_transaction(amount, "DEPOSIT", description)

        return self._balance


    def withdraw(self, amount: float, description: str = "Withdrawl"):
        # Withdraw money - with validation
        if amount <= 0:
            raise ValueError("Withdrawl amount must be positive")

        if amount >= self._balance:
            raise ValueError("Insufficient funds")

        self._balance -= amount
        self._add_transaction(-amount, "WITHDRAWL", description)

        return self._balance

    def get_balance(self) -> float:
        # Read-only access to balance
        return self._balance
    
    # Private helper methods - implementation detials ~ meant to use internally & not expose to the user
    def _add_transaction(self, amount: float, trans_type: str, description: str):
        # Internal method to record transactions
        transaction = Transaction(amount, trans_type, description)
        self._transactions.append(transaction)




    
# Problem of this code
if __name__ == "__main__":
    account = BankAccount("Alice", 100)

    print(f"Initial balance $: {account}")

    # Problem 1: Can directly modify balance without validation ~ So direct manipulation
    account.balance = -500 # Negative balance?!

    # Problem 2: Can bypass business logic
    account.balance = 1000000 # Instantiate millionaire!

    # Problem 3: Can corrupt internal state
    account.transctions = "not a list anymore"

    # Problem 4: If we can change internal representation, all code breaks
    # For example: If I want to store balance in cents instead of dollars




"""
3) Loose Coupling & Modularity
Depend on abstractions, not concrete implementations

Coupling -> How tightly things are connected together

Typically when I write code, I don't want to couple things together too much
means I don't want to write functions that rely on other functions or rely on
specific implementations or class - all of these are tight all of these components
in together. I should make things as flexible as possible and purely rely in
internal state and logic

    - Use interfaces/abstract base classes
    - Inject dependencies (don't instantiate internally)
    - Components should be swappable (instead of email service work with 1 email provider ~ can work with many email provider)
    - Minimize inter-module dependencies

Ask myself: Can I test this component without instantiating half my system?


Problem:
1) Orderprocessor is tightly coupled to EmailSender ~ Any time I send an email I have to use EmailSender
2) Can't test without OrderProcessor without sneding emails
"""

# Bad: Tightly coupled - Components directly depend on each other

class EmailSender:
    #Email implementation
    def send_email(self, to: str, subject: str, body: str):
        print(f"Sendint email to {to}: {subject}")

class OrderProcessor:
    #Tightly coupled to EmailSender

    def __init__(self):
        # Couple EmailSender inside here
        # Hard-coded dependency - TIGHT COUPLING
        self.email_sender = EmailSender() # Bad, bcz if removed -> no longer work
        # Also I cant change EmailSender class that I will use inside here
        # Instead I would email_sender as parameter - rather relying on an exact class implementation
        # I rely on abstract class which enforces or define interface that any emails sender needs to have


# GOOD: loosely coupled application ~ decoupled application
"""
if __name__ == "__main__":
EMAIL NOTIFCATIONS
email_notifier = EmailNotifier()
processor = OrderProcessor(email_notifer)
processor.process_order(...)

SMS NOTIFCATIONS
sms_notifier = SMSNotifier()
processor = OrderProcessor(sms_notifer)

Reason they decoupled because we define abstract class



"""


# Abstract intefrace for notifcations -- enable loose coupling
# notifer.py
from abc import ABC, abstractmethod



class Notifier(ABC):
    # Abstract base class - define the interface

    # Send method must look like this
    @abstractmethod # this decorator enforces that anything that inherit from it, it wants to implement this class must have this method
    def send(self, recipient: str, subject: str, message: str):
        # send notification
        pass


# sms_notifier
# SMS implementation of Notifier interface
#from notifier import Notifier -> it inherit from abstract class and implement my SMS setting



class SMSNotifer(Notifier):
    """Concrete implementation for SMS"""

    def send(
            self,
            recipient: str,
            subject: str,
            message: str
    ):
        print(f"SMS to: {recipient}")

# order_processor.py

# from notifier import Notifier

# So SMS notifier or email notifier can be used interchangeably inside my order_porcessor - rely on notifer:Notifier abstract class 

# Pass Notifer as parameter type 
class OrderProcessor:
    #Loosely coupled - depends on Notifier interface

    def __init__(self, notifier: Notifier):
        # Dependency injected - LOOSE COUPLING
        self.notifier = notifier

    # I can use send method indise here
    def process_order(self, order_id: int, customer_contact: str):
        # Apply business logic ~ Validating order, charging payment, updating inventory

        # Notification - Uses injected Notifier (any implementation!)
        # It is loosely coupled
        self.notifier.send(
            customer_contact,
            f"Order {order_id} confirmed",
            "Thank you for your order!"
        )

#This allow me to use interchangeably
if __name__ == "__main__":
    print("Email Notifier")
    email_notifier = EmailNotifier()
    processor = OrderProcessor(email_notifier)
    processor.process_order(...)

    print("SMS Notification")
    sms_notifer = SMSNotifer()
    processor = OrderProcessor(sms_notifer)
    processor.process_order(...)

    """
    BENEFITS:
        - OrderProcessor doesn't know or care HOW notification is sent
        - Can easily swap email for SMS (or add more)
        - Easy to test with mock notifer
        - Can compose multiple notifier
        - NO changes to OrderProcessor when adding new notification types
        - Each module is independent and reusable
    
    """




"""
4) Reusability and Extensibility

Open for extension

Ask myself: Can I add new functionality without editing existing code?

"""

# BAD: Hard-coded - Not reusable or extensible 
# Monolithic report generator - hard to extend & add functionality ~ Example: inside method contain many elif conditions

#GOOD: Extensible and Reusable design using Strategy pattern
from abc import ABC, abstractmethod
from typing import Dict, List

# 1
# Define abstract base class - Defines that anything that wants to be a ReportFormatter --> must have this format() method
class ReportFormatter(ABC):
    """
    Abstract formatter - define the interface
    """

    @abstractmethod
    def format(self, data: list[Dict]) -> str:
        """Format data into a report"""
        pass


# 2
# They are all implementing their own format method
# We write all the individual formatters based on the abstract interface
class TextFormatter(ReportFormatter):
    # Reusable text formatter

    # Able to write different methods that we need
    def format(self, data: List[Dict]) -> str:
        for item in data:
            print(item)

        return True


class CSVFormatter(ReportFormatter):
    # Reusable CSV formatter

    def format(self, data: List[Dict]) -> str:
        if not data:
            return ""

        # Extract headers from first item
        headers = data[0].keys()

        for item in data:
            values = [str(item(h)) for h in headers]

        return True

# 3
# In ReportGenerator - I can take any report formatter and then I can generate a report by that formatter: self.formatter]
# Goa: No changes will be made to my report generator --> but I simply write another report formatter and pass that in ReportGenerator and it can generate a report
# It is extensible without needing to be modified
class ReportGenerator:
    # Generator that works with any formatter - extensible

    def __init__(self, formatter: ReportFormatter):
        self.formatter = formatter

    def generate(self, data: List[Dict]) -> str:
        # Generate report using the configured formatter
        return self.formatter.format(data)

    def set_formatter(self, formatter: ReportFormatter):
        # Change formatter at runtime
        self.formatter = formatter

if __name__ == "__main__":

    # Create generator with text formatter
    generator = ReportGenerator(TextFormatter())

    # Text format 
    generator.generate(data)



    # switch to CSV format
    generator.set_formatter(CSVFormatter())

    generator.generate(data)

    # switch to HTML, JSON and so on



"""
5) Portability
Write once, run anywhere

Ask myself: Will this work on linux, windows, and mac?

- use cross-platform libraries (pathlib, not os.path)
- Environment variables for configuration
- Avoid platform-specific assumption


Not portrable - tied to specific platform and environment

"""


# Let see the bad file handler - that many developer do the same mistakes
import os

class DataProcessing:
    # Not portable - hard-coded Windows path


    def __ini__(self):
        # Hard code the input and output directories
        # This code will never work on any machine other than ours
        # Reason: I wi ll change directory manually - and this a windows file path ~ we make it windows style path
        # We should use dynamic path 
        self.input = "C:\\Users\\John\\Documents\\data"
        self.output = "C:\\Users\\John\\Documents\\output"


        # Hard-coded database connection
        self.db_host = "localhost"
        self.db_port = 5432

        # Hard-coded API endpoint
        self.api_url = "http://localhost:8000/api"



    def processing_file(self, filename: str):
        # Building path with hard-coded separator
        input_path = self.input_dir + "\\" + filename
        output_path = self.output_dir + "\\" + filename


        print(f"Processing: {input_path}")
        print(f"Output: {output_path}")

        # So this code will only work on windows especially using separator //


# GOOD: Portable across platforms and environment
# Create environment variable file - I put all the dynamic value that I may need to change depending on the evironment which I am running

"""
Example environment variable configuration file
Copy to .env and customize for your environment

# File path (cross-platform)
INPUT_DIR = ./data
OUTPUT_DIR = ./output

# Database Configuration
DB_HOST = localhost
DB_PORT = 5432
DB_USER = myapp
DB_PASSWORD = secret


# API configuration
API_URL = http://localhost:8000/api
API_TIMEOUT = 30

# Environment Variable
ENVIRONMENT = development

So I have database information, api information, I have current environment, and file directory that works cross platform
So I rely on environment variable rather than hard-coded values

"""

import os
from pathlib import Path
from typing import Optional

# We make is dynamic to any environment
class Config:
    # Configuration abstraction - can load from env, file, etc ...

    def __init__(self):
        # Use enironment variables  - I use Path variable from the pathlib which make this dynamic and works cross-platform
        self.input_dir = Path(os.getenv("INPUT_DIR", "./data"))
        self.output_dir = Path(os.getenv("OUTPUT_DIR", "./output"))

        self.db_host = os.getenv("DB_HOST", "localhost")
        self.db_port = int(os.getenv("DB_PORT", "5432"))



"""
6) Defensibility

Fail fast, fail safe, fali loud

Defend our code from bad input provided 


Ask myself: Waht the worst that coulkd happen with bad input
"""

# Fail-fast: Validate input immediately
amount = 10
if amount <=0:
    raise ValueError('Amount must be positive')


# Least privilage: Store log only whats necessary
# Store: "****_****_****_1234"
# NOT: Full credit card number 

# Safe default values: secure defaults
debug_mode = False # Not True!
timeout = 30 # Not None