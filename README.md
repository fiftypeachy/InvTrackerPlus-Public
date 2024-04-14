# InvTrackerPlus

#### Video Demo: https://youtu.be/E5n4JA0BXC4

## Description

**InvTrackerPlus** uses **Django** as its framework, and SQLite3 as its database. I opted to use Django instead of Flask to take advantage of its **Object Relational Mapping (ORM)** capabilities out of the box, instead of having to rely on third party packages such as [SQLAlchemy](https://www.sqlalchemy.org/).

**InvTrackerPlus** is an investment portfolio tracker, that allows users to add transactions (buy/ sell) to keep track of them. The website will then keep track of their unrealised and realised profits (or losses). Currently, the site is only limited to US listed stocks. 

**InvTrackerPlus** caters to many people from around the world. In the settings, you can change the home currency to the ten most common currencies in the world, and your total account value will be converted to that.

## How do I run this programme?
1. Have a Python environment running. I used the version 3.11.8 to develop this. Download [Python 3.11.8 here](https://www.python.org/downloads/release/python-3118/).
2. Clone this repository into a command-line interface (such as bash) by running
   ```bash
   git clone https://github.com/fiftypeachy/InvTrackerPlus-Public.git
   ```
3. and cd into the cloned repository by executing
   ```bash
   cd InvTrackerPlus-Public
   ```
4. Execute
   ```bash
   pip install -r requirements.txt
   ```
   to install the necessary dependencies.
5. Execute
   ```bash
   python manage.py runserver
   ```
   to run the webpage. Interact with the page at http://127.0.0.1:8000/.

## Motivation behind this project
I was tired of having to manually key in my own data into a stock tracker application or an Microsoft Excel Workbook, so I thought I should create an application that allows me to perhaps automate the process of data input. 

Essentially the end goal was to be able to upload a statement of sorts and a function will parse the statement document, and update the internal database. How easy will that be to track dividends, fees and the nitty gritty details of everything.

Though I have yet to implement this feature, this application has the essential parts of an average stock tracker. It has been a hell of a ride developing this. I needed to search far and wide through Django's documentation to understand how everything works from the Models to the Forms. At first I started out with Flask since it was a continuation from week 9's problem set, and thought SQLAlchemy will help me in this project, but I found that I did not really understand its documentation. That was why I changed to Django and I did not look back since. 

In the near future, I will probably implement the feature that I have always yearned for, probably through another framework. Ideally React Native since a stock tracker should be mobile friendly.

## My Models (in [base/models.py](base/models.py))
### 1. ```Stock```
#### Attributes: ```ticker```, ```exchange```, ```price```, ```last_updated```
```ticker``` is unique to each ```Stock``` object.

```exchange``` is stored in the database so that when I web scrape the price off Google Finance, it does not need to guess which exchange the ticker is traded in. 

```price``` is stored in the database to make it easier for calculations such as total account value and outstanding profits and losses.

```last_updated``` is stored in the database to reduce the number of times I update price, since updating price is a rather slow process, (as I use web scraping).

>  **Feature to work on:** Perhaps I could use Asynchronous JavaScript to load the prices.

#### Initialisation
I designed the initialisation process in a way that ensures that the ticker that the user inputs is one that is listed on Google Finance, before creating the stock object. In ```create_stock_if_valid``` function, it takes in a ```ticker``` argument, usually from a user's input, and pass it into ```get_stock_price``` function. ```get_stock_price``` will realise that it receives a new ticker that does not have an exchange explicitly listed, so it will iterate through the 3 common exchanges, i.e. NASDAQ, NYSE and NYSEARCA, and check which of the few exchanges will result in a valid stock (which has a stock price). If the ticker is valid, a new stock object will be created, storing the ```ticker```, ```price``` and ```exchange``` which the stock is traded in. 

#### Maintaining the price
In order to ensure that price is up to date everytime it is accessed, I used the ```@property``` decorator, where the stock instance calls ```update_stock_info()``` function, to update the price of the stock instance, before returning the updated price to wherever the price is accessed.

```update_stock_info()``` uses the ```last_updated``` attribute to determine if a reasonable amount of time has passed (default is 5 minutes) where the stock price should be updated. If ```last_updated``` is more than 5 minutes ago, then the price will be updated again, calling the ```get_stock_price``` function which web scrapes Google Finance. The function also takes into account whether the price was last updated during market closure timings, and does not update the price any more during the market closure timings (where price stays the same). This reduces the need for unnecessary updating of the price, saving resources.


### 2. User
#### Attributes: ```username```, ```email```, ```cash```, ```tz```, ``hc``

I chose to have a custom user model so that I can add ```cash```, ```tz```(timezone) and ```hc```(home currency) which are all very relevant to the user. Furthermore, I do not intend on making this application (base) reusable so there are no constraints with editing the user model.

#### ```get_holdings(self)``` method
Using the ability to get all OwnedStock objects that are related to the user, I filtered through the OwnedStock objects where the user currently holds a position in and return the list of the OwnedStock objects.

#### ```get_nav(self, holdings)``` method
NAV stands for ```Net Account Value``` and is calculated by summing up all the floating values of the positions owned by the user, and the user's cash. 


### 3. OwnedStock
#### Attributes: ```user```, ```current_quantity```, ```stock```, ```average_cost_price```, ```realised_pnl```
```OwnedStock``` objects are identified by a unique ```stock``` owned by a specific ```user``` with a ```current_quantity``` attribute.

#### ```update_instance(self)``` method
Calculates and updates the current quantity, average cost price and realised profits and losses based on the transaction history.
Adopts a first in first out approach. i.e. the earlier the stock is bought, the greater the priority it will be sold first.

Firstly, we calculate the ```currently owned quantity```, which is given by
```currently owned quantity``` = ```total buy quantity``` - ```total sell quantity```

Secondly, we calculate the ```cost of the currently owned stocks```. This is given by
```total cost``` = ```initial cost of all bought stocks``` - ```initial cost of stocks that were already sold```.
```initial cost of all bought stocks``` = sum of the ```unit price of each transaction```, and the ```quantity of each transaction``` for all stocks in the buy direction.
To calculate the ```initial cost of stocks that were already sold```, I recursively checked if the unconsidered quantity was less than or equal to the quantity of the buy transaction with the greatest priority (earliest unconsidered buy transaction) if true, I add the cost of the stocks based on the price of the buy transaction to the recursive sum, and return it. Otherwise, I will call recursive function again.

Finally, ```total_cost``` can be calculated, and ```average_cost_price``` is simply just the ```total_cost``` divided by the ```total quantity```.

To calculate the ```realised profits and losses```, I calculated the revenue of the stock that has been sold. The ```realised profits and losses``` is the ```total revenue``` - ```initial cost of stocks that are sold```


### 4. Transaction
#### Attributes: ```user```, ```owned_stock```, ```datetime```, ```unit_price```, ```quantity```, ```direction```

Each ```transaction``` by a ```user``` has an ```owned_stock``` tied to it with the relevant information.

```transaction``` objects are used to calculate the ```average_cost_price``` and the ```realised_pnl``` (realised profits and losses) of ```OwnedStock``` object.

It also allows the user to keep track of their past entries.

Each time a user buys or sells a stock, the ```create_transaction_and_update_owned_stock()``` function should be called, which creates ```transaction``` and update ```ownedstock``` objects based on the user's input. 

### 5. Transfer
#### Attributes: ```user```, ```method```, ```value```, ```old_cash```, ```new_cash```, ```datetime```

```Transfer``` objects keep track of transfers made by ```user```.

It allows the user to keep track of the cash that they hold. 

> **Possible feature:** To add an option in the transaction form to deduct cash from user's cash balance when purchasing stocks, or similarly add cash to user's cash balance when selling stocks.

## My Views (in [base/views.py](base/views.py))
### 1. Home Page
Users can view their holdings, net account value, total unrealised profits and losses as well as total realised profits and losses.

Toggling the accordian shows the corresponding transactions relevant to the selected stock that the user owns.

### 2. Search Page
When user inputs in a ticker, depending on whether the ticker has been queried before, it will check with Google Finance if it is a valid ticker, and return the relevant information, and a form to add a buy/ sell transaction for the particular stock.

### 3. Transfer Page
Enables user to set, withdraw, or deposit a variable amount of cash.

### 4. History Page
Displays the transaction and transfer history for all stocks and transfers.

### 5. Settings Page
Allows users to edit their user profile, which consists of
1. Password
2. Username
3. Email
4. Home Currency
5. Timezone

### 6. Transact Route
Updates the database based on user's input transaction in the form displayed in the search route.

### 7. Delete Transaction Route
Updates the database when user requests to delete a transaction.


## Features to work on (in the foreseeable future)

1. updating of prices uses a datetime calculation of recency of update, stored in database ✅
2. set all foreign keys to cascade on delete. ✅
3. remove all unnecessary "null=True"s 
4. implement an error page
5. implement a date and time selector in buy and sell routes ✅
6. use GET instead of POST for searching route ✅
7. implement ASYNC for searching
8. implement ability to delete transactions ✅

## Credits
Bits and pieces of code were inspired from ChatGPT (really amplified my productivity).

Free images used on registration pages sourced from [Pexels](https://www.pexels.com/).
