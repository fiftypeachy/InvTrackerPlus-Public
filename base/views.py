from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, PasswordChangeView
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .forms import (
    CustomAuthenticationForm,
    CustomChangePasswordForm,
    MyUserCreationForm,
    TransactionForm,
    TransferForm,
    UserSettingsForm,
)
from .models import OwnedStock, Stock, Transaction, TransactionManager, Transfer, User
from .templatetags.base_extras import usd


# Create your views here.
class CustomLoginView(LoginView):
    form_class = CustomAuthenticationForm


class CustomPasswordChangeView(PasswordChangeView):
    form_class = CustomChangePasswordForm
    template_name = "registration/password_change.html"


def register(request):
    form = MyUserCreationForm()

    if request.method == "POST":
        form = MyUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=True)
            login(request, user)
            return redirect("base:home")
        else:
            messages.error(request, "An error occurred during registration")

    return render(request, "registration/register.html", {"form": form})


def logout_page(request):
    logout(request)
    return redirect("base:login")


@login_required()
def home(request):
    user: User = request.user
    holdings = user.get_holdings()
    nav = user.get_nav(holdings)

    total_unrealised_pnl = sum(
        [
            (ownedStock.stock.price - ownedStock.average_cost_price)  # type:ignore
            * ownedStock.current_quantity
            for ownedStock in holdings
        ]
    )
    total_realised_pnl = sum([ownedStock.realised_pnl for ownedStock in holdings])  # type: ignore

    context = {
        "holdings": holdings,
        "total": nav,
        "tup": total_unrealised_pnl,
        "trp": total_realised_pnl,
    }
    return render(request, "base/home.html", context)


@login_required
def search(request):
    ticker = request.GET.get("ticker").upper() if request.GET.get("ticker") else None
    if not ticker:
        return render(request, "base/search.html", context={})

    try:
        stock = get_object_or_404(Stock, ticker=ticker)
    except Http404:
        # if 404, means call API and create new stock object
        stock = Stock.create_stock_if_valid(ticker=ticker)

    if not stock:
        messages.error(request, "Ticker is invalid.")
        return redirect("base:search")

    q = request.user.ownedstock_set.filter(stock=stock)
    ownedstock = q.get() if q else None
    transactions = ownedstock.transaction_set.all() if ownedstock else None
    form = TransactionForm()

    context = {
        "stock": stock,
        "ownedstock": ownedstock,
        "form": form,
        "transactions": transactions,
    }
    return render(request, "base/results.html", context=context)


@login_required
def transfer(request):
    form = TransferForm()
    if request.method == "POST":
        # Get the user, method, and value from the form
        form = TransferForm(request.POST)
        if form.is_valid():
            user: User = request.user
            method = form.cleaned_data["method"]
            value = form.cleaned_data["value"]

            if method == "deposit":
                new_cash = user.cash + value
            elif method == "withdrawal":
                if value > user.cash:
                    return HttpResponse(
                        "Bad request: You want to withdraw more cash than you own."
                    )
                new_cash = user.cash - value
            elif method == "set":
                new_cash = value
            else:
                return HttpResponse("The method is invalid")

            now = timezone.now()

            Transfer.objects.create(
                user=user,
                method=method,
                old_cash=user.cash,
                new_cash=new_cash,
                datetime=now,
                value=value,
            )

            user.cash = new_cash

            user.save()

            # Flash message upon next request
            def tense(method):
                if method == "deposit":
                    return "deposited into"
                elif method == "withdrawal":
                    return "withdrawn from"
                elif method == "Set":
                    return "set for"

            messages.success(
                request, f"{usd(value)} has been {tense(method)} your account!"
            )

            return redirect("base:home")
        else:
            messages.error(request, "You have entered invalid values!")

    return render(request, "base/transfer.html", {"form": form})


@login_required
def history(request):
    transactions = request.user.transaction_set.all()
    transfers = request.user.transfer_set.all()
    context = {"transactions": transactions, "transfers": transfers}
    return render(request, "base/history.html", context=context)


@login_required
def settings(request):
    if request.method == "POST":
        form = UserSettingsForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
        messages.success(request, "Your profile has been updated!")
    form = UserSettingsForm(instance=request.user)

    return render(request, "base/settings.html", context={"form": form})


@require_POST
def transact(request, pk):
    form = TransactionForm(request.POST)

    if form.is_valid():
        user = request.user
        stock = Stock.objects.get(id=pk)
        quantity = form.cleaned_data["quantity"]
        datetime = form.cleaned_data["datetime"]
        price = form.cleaned_data["unit_price"]
        direction = form.cleaned_data["direction"]

        TransactionManager.create_transaction_and_update_owned_stock(
            user=user,
            stock=stock,
            datetime=datetime,
            unit_price=price,
            quantity=quantity,
            direction=direction,
        )

        # Flash message upon next request
        def past_tense_direction(direction=direction):
            if direction == "buy":
                return "bought"
            elif direction == "sell":
                return "sold"
            else:
                return direction

        messages.success(
            request,
            f"{quantity} {stock.ticker}(s) have been {past_tense_direction()} at {usd(price)} each.",
        )

        return redirect("base:home")
    else:
        messages.error(
            request,
            "Something wrong happened when you attemptted to add a transaction.",
        )
        return redirect("base:results", pk)


@require_POST
def delete_transaction(request, pk):
    transaction = get_object_or_404(Transaction, pk=pk)
    stock = transaction.owned_stock.stock.ticker
    transaction.delete()
    messages.success(
        request,
        f"Transaction with Transaction ID {pk} (ticker: {stock}) has successfully been deleted.",
    )

    # Get the referrer URL from the request headers
    referrer_url = request.META.get("HTTP_REFERER")

    # If the referrer URL exists and it's not the delete transaction URL,
    # redirect back to the referrer URL. Otherwise, redirect to the home page.
    if referrer_url and referrer_url != request.build_absolute_uri():
        return redirect(referrer_url)
    else:
        return redirect("base:home")
