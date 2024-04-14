import re
from datetime import datetime, time, timedelta
from decimal import Decimal
from types import NoneType

import requests
from bs4 import BeautifulSoup
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ObjectDoesNotExist
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q
from django.db.models.query import QuerySet
from django.utils import timezone

from .model_choices import EXCHANGE_CHOICES, HC_CHOICES, TZ_CHOICES


# Helper functions
def is_outside_trading_hours():
    current_time = timezone.now().astimezone(timezone.get_default_timezone()).time()
    market_open_time = time(hour=9, minute=30)
    market_close_time = time(hour=16)

    # Check if the current time is before market open or after market close
    return current_time < market_open_time or current_time >= market_close_time


def is_after_market_close(last_updated):
    now = timezone.now().astimezone(timezone.get_default_timezone())

    # if current time is before 4pm,
    if now.hour < 16:
        now = now - timedelta(days=1)

    # Assuming market closed on the nearest 4pm that has passed
    market_closed = now.replace(hour=16, minute=0, second=0, microsecond=0)

    # if last_updated after market closed
    if last_updated > market_closed:
        return True

    return False


# Create your models here.
class PositiveDecimalField(models.DecimalField):
    def __init__(self, *args, **kwargs):
        kwargs["validators"] = [MinValueValidator(0)]
        super(PositiveDecimalField, self).__init__(*args, **kwargs)


class CurrencyConversionRate(models.Model):
    cfrom = models.CharField(max_length=3)
    cto = models.CharField(max_length=3)
    _ccrate = PositiveDecimalField(max_digits=20, decimal_places=6, default=Decimal())

    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ["cfrom", "cto"]

    @property
    def ccrate(self) -> Decimal:
        # If currency conversion rate (_ccrate) was updated within the past 30 mins and if the rate isn't 0, return the rate.
        if (
            timezone.now() - self.last_updated < timezone.timedelta(minutes=30)
            and self._ccrate
        ):
            return self._ccrate

        # URL of the webpage
        url = f"https://www.xe.com/currencyconverter/convert/?Amount=1&From={self.cfrom}&To={self.cto}"

        # Send a GET request to the URL
        response = requests.get(url)

        # Parse the HTML content of the webpage
        soup = BeautifulSoup(response.text, "html.parser")

        rate = soup.find("p", {"class": "sc-1c293993-1 fxoXHw"})

        if rate:
            match = re.match(r"^\d+\.\d+", rate.text)  # type: ignore

        if match:
            self._ccrate = Decimal(match.group())
            self.save()
            print(
                f"Web Scraped rate {self.cfrom}{self.cto} successfully at {self._ccrate}."
            )
        else:
            print(f"Web Scraped rate {self.cfrom}{self.cto} unsuccessfully.")
            if not self._ccrate:
                self._ccrate = Decimal()
                self.save()

        return self._ccrate
    
    def __str__(self):
        return f"{self.cfrom}/{self.cto} has an exchange rate of {self.ccrate}."


class Stock(models.Model):
    ticker = models.CharField(max_length=10, unique=True)
    exchange = models.CharField(max_length=10, choices=EXCHANGE_CHOICES, null=True)
    _price = PositiveDecimalField(decimal_places=2, max_digits=10)
    last_updated = models.DateTimeField(auto_now=True)

    def clean(self):
        super().clean()

        if self.ticker:
            self.ticker = self.ticker.upper()

    @property
    def price(self):
        self.update_stock_info()
        return self._price

    @classmethod
    def get_stock_price(
        cls, ticker: str, exchange: str | NoneType = None
    ) -> tuple[Decimal, str | None] | None:
        ticker = ticker.upper()

        def web_scrape(ticker, exchange) -> Decimal | NoneType:
            # URL of GOOGLE FINANCE Page
            url = f"https://www.google.com/finance/quote/{ticker}:{exchange}"

            # Send a GET request to the URL
            response = requests.get(url)

            # Parse the HTML content of the webpage
            soup = BeautifulSoup(response.text, "html.parser")

            latest = soup.find("div", class_="YMlKec fxKbKc")

            if latest:
                match = re.search(r"\d+\.\d{2}", latest.text)  # type: ignore
            else:
                print(f"No match for {ticker}:{exchange} in web scraping.")
                return

            if match:
                print(
                    f"Web Scraped {ticker}:{exchange} successfully at the latest price of {latest.text}."
                )
                return Decimal(match.group())

            else:
                print(f"Web Scraped {ticker}:{exchange} unsuccessfully.")
                return Decimal()

        # If the exchange where ticker is traded in is unknown,
        if not exchange:
            for choice in EXCHANGE_CHOICES:
                exchange = choice[0]
                price = web_scrape(ticker, exchange)

                if price:
                    return price, exchange

        # If the exchange where ticker is traded in is known,
        else:
            price = web_scrape(ticker, exchange)
            if price:
                return price, exchange

        return None

    @classmethod
    def create_stock_if_valid(cls, ticker):
        ticker = ticker.upper()

        price = cls.get_stock_price(ticker)  # type: ignore

        if price:
            return cls.objects.create(ticker=ticker, _price=price[0], exchange=price[1])

        return None

    def update_stock_info(self):
        # if time now is in a time when market is closed, AND last_update is after the time market was closed, just return.

        if (
            is_outside_trading_hours()
            and is_after_market_close(self.last_updated)
            or timezone.now() - self.last_updated < timezone.timedelta(minutes=5)
        ):
            return

        price = self.get_stock_price(ticker=self.ticker, exchange=self.exchange)

        if price:
            self._price = price[0]
            self.exchange = price[1]
            self.save()
            print(f"Updated {self.ticker}'s price")
        else:
            # Exchange is wrong
            print(f"Check exchange if it is correct for {self.ticker}")

    def __str__(self):
        return f"{self.ticker} has a price of {self._price}."


class User(AbstractUser):
    username = models.CharField(max_length=100, unique=True)
    email = models.EmailField(unique=True)
    cash = PositiveDecimalField(decimal_places=2, max_digits=10, default=0.00)
    tz = models.CharField(verbose_name="Timezone", max_length=50, choices=TZ_CHOICES)
    hc = models.CharField(
        verbose_name="Home Currency", max_length=50, choices=HC_CHOICES, default="SGD"
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username", "tz"]

    class Meta:
        ordering = ["username"]

    def get_holdings(self):
        owned_stocks: QuerySet[OwnedStock] = self.ownedstock_set.filter(  # type: ignore
            current_quantity__gt=0
        ).order_by("stock__ticker")

        return owned_stocks

    def get_nav(self, holdings):
        return (
            sum(
                [
                    ownedStock.stock.price * ownedStock.current_quantity  # type: ignore
                    for ownedStock in holdings
                ]
            )  # type: ignore
            + self.cash
        )

    def clean(self):
        super().clean()
        if self.username:
            self.username = self.username.lower()
        if self.email:
            self.email = self.email.lower()

    def __str__(self):
        return f"{self.email} has {self.cash} and owns {self.get_holdings()}"


class OwnedStock(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    current_quantity = PositiveDecimalField(max_digits=10, decimal_places=2, null=True)
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE)
    average_cost_price = PositiveDecimalField(
        max_digits=10, decimal_places=2, null=True
    )
    realised_pnl = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal("0.0")
    )

    class Meta:
        ordering = ["stock"]

    def update_instance(self):
        """
        Calculates and updates the current quantity, average cost price and realised profits and losses.
        based on the transaction history.
        Adopts a first in first out approach. i.e.
        The earlier the stock is bought, the greater the priority it will be sold first.

        Firstly, we calculate the currently owned quantity, which is given by
        currently owned quantity = total buy quantity - total sell quantity

        Secondly, we calculate the cost of the currently owned stocks. This is given by
        total cost = initial cost of all bought stocks - initial cost of stocks that were already sold.
        initial cost of all bought stocks = sum of the unit price of each transaction, and the quantity of each transaction for all stocks in the buy direction.
        initial cost of stocks that were already sold = sum of the unit price of each transaction and the quantity of each transaction for the left over stocks that user owns.
        """
        total_buy_quantity: Decimal = (
            self.transaction_set.filter(direction="buy").aggregate(  # type: ignore
                models.Sum("quantity")
            )["quantity__sum"]
            or 0
        )  # type: ignore
        total_sell_quantity: Decimal = (
            self.transaction_set.filter(direction="sell").aggregate(  # type: ignore
                models.Sum("quantity")
            )["quantity__sum"]
            or 0
        )  # type: ignore

        total_quantity = total_buy_quantity - total_sell_quantity

        initial_cost_of_all_bought_stocks = sum(
            transaction.unit_price * transaction.quantity
            for transaction in self.transaction_set.filter(direction="buy")  # type: ignore
        )

        list_of_buy_transactions: QuerySet[Transaction] = self.transaction_set.filter(  # type: ignore
            direction="buy"
        ).all()

        def calculate_cost(
            unconsidered_quantity=total_sell_quantity,
            row=0,
            recursive_sum: Decimal = Decimal(),
        ) -> Decimal:  # type: ignore
            rows_bought_qty: Decimal = list_of_buy_transactions[row].quantity
            rows_bought_price: Decimal = list_of_buy_transactions[row].unit_price

            if unconsidered_quantity <= rows_bought_qty:
                recursive_sum += unconsidered_quantity * rows_bought_price
                return recursive_sum
            elif unconsidered_quantity > rows_bought_qty:
                recursive_sum += rows_bought_qty * rows_bought_price
                unconsidered_quantity -= rows_bought_qty
                return calculate_cost(unconsidered_quantity, row + 1, recursive_sum)

        initial_cost_of_stocks_that_are_sold: Decimal = calculate_cost()

        total_cost = (
            initial_cost_of_all_bought_stocks - initial_cost_of_stocks_that_are_sold
        )

        if total_quantity > 0:
            self.current_quantity = total_quantity
            self.average_cost_price = total_cost / total_quantity
        else:  # If else is to prevent the ZeroDivisionError, where total_quantity = 0.
            # Completely closed position.
            self.current_quantity = 0
            self.average_cost_price = 0

        # To calculate Realised Profits and Losses
        if total_sell_quantity == 0:
            self.save()
            return

        total_revenue: Decimal = sum(
            transaction.unit_price * transaction.quantity
            for transaction in self.transaction_set.filter(direction="sell")  # type: ignore
        )
        self.realised_pnl = total_revenue - initial_cost_of_stocks_that_are_sold
        self.save()

    @classmethod
    def get_owned_stock(cls, stock: Stock, user: User):
        query = OwnedStock.objects.filter(
            Q(user=user), Q(stock=stock), Q(current_quantity__gt=0)
        )
        try:
            owned_stock = query.get()
        except ObjectDoesNotExist:
            return None
        else:
            return owned_stock

    def __str__(self):
        return f"{self.user.email} owns {self.current_quantity} of {self.stock.ticker} at an average cost price of {self.average_cost_price} each."


class Transaction(models.Model):
    DIRECTION_CHOICES = [
        ("buy", "Buy"),
        ("sell", "Sell"),
    ]
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    owned_stock = models.ForeignKey(OwnedStock, on_delete=models.CASCADE)
    datetime = models.DateTimeField(verbose_name="Date & Time")
    unit_price = PositiveDecimalField(max_digits=10, decimal_places=2)
    quantity = PositiveDecimalField(max_digits=10, decimal_places=2)
    direction = models.CharField(max_length=10, choices=DIRECTION_CHOICES)

    class Meta:
        ordering = ["datetime"]

    def __str__(self):
        return f"{self.user.email} {self.direction}s {self.quantity} {self.owned_stock.stock.ticker}s at {self.unit_price} each."


class TransactionManager:
    @staticmethod
    def create_transaction_and_update_owned_stock(
        user: User,
        stock: Stock,
        datetime,
        unit_price: Decimal,
        quantity: Decimal,
        direction,
    ):
        """
        Creates OwnedStock, use it to create Transaction object, and updates
        OwnedStock object's quantity and average cost price attributes.
        """
        # Create OwnedStock if not created
        owned_stock, created = OwnedStock.objects.get_or_create(user=user, stock=stock)

        # Create Transaction
        transaction = Transaction.objects.create(
            user=user,
            owned_stock=owned_stock,
            datetime=datetime,
            unit_price=unit_price,
            quantity=quantity,
            direction=direction,
        )

        owned_stock.update_instance()

        return transaction, owned_stock


class Transfer(models.Model):
    METHODS = [("withdrawal", "Withdrawal"), ("deposit", "Deposit"), ("set", "Set")]
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    method = models.CharField(max_length=10, choices=METHODS)
    value = PositiveDecimalField(max_digits=10, decimal_places=2)
    old_cash = PositiveDecimalField(max_digits=10, decimal_places=2)
    new_cash = PositiveDecimalField(max_digits=10, decimal_places=2)
    datetime = models.DateTimeField()

    def __str__(self):
        return f"{self.user.email} {self.method}"
