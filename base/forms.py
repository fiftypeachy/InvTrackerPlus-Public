import itertools

from django import forms
from django.contrib.auth.forms import (
    AuthenticationForm,
    PasswordChangeForm,
    UserCreationForm,
)

from .models import Stock, Transaction, Transfer, User

# from django.forms.utils import flatatt
# from django.forms.widgets import Select
# from django.utils.encoding import force_text


# class CustomSelect(Select):
#     def render_option(self, selected_choices, option_value, option_label):
#         option_attrs = self.build_attrs(self.attrs, {"value": option_value})
#         if option_value in selected_choices:
#             option_attrs.update({"selected": "selected"})

#         # Add 'disabled' attribute to the first option
#         if not selected_choices and option_value == "":
#             option_attrs["disabled"] = "disabled"

#         return "<option%s>%s</option>" % (
#             flatatt(option_attrs),
#             force_text(option_label),
#         )


class BaseForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super(BaseForm, self).__init__(*args, **kwargs)
        # Add the form-control or form-select class to all fields
        for field_name in self.fields:
            field = self.fields[field_name]
            if hasattr(field, "choices") and field.choices:
                choices_length = sum(1 for _ in field.choices)
                if choices_length > 4:
                    # field.widget = CustomSelect(attrs={"class": "form-select"}, choices=field.choices)
                    field.widget.attrs["class"] = "form-select"
                else:
                    field.widget = forms.RadioSelect(
                        choices=itertools.islice(field.choices, 1, None)  # type: ignore
                    )
            else:
                field.widget.attrs["class"] = "form-control"


class BaseModelForm(forms.ModelForm, BaseForm):
    pass


class MyUserCreationForm(UserCreationForm, BaseModelForm):

    class Meta:
        model = User
        fields = ["email", "username", "tz", "password1", "password2"]


class CustomAuthenticationForm(AuthenticationForm, BaseForm):
    pass


class CustomChangePasswordForm(PasswordChangeForm, BaseForm):
    pass


# class TickerSearchForm(BaseModelForm):
#     class Meta:
#         model = Stock
#         fields = ["ticker"]


class TransactionForm(BaseModelForm):

    class Meta:
        model = Transaction
        fields = ["datetime", "quantity", "unit_price", "direction"]
        widgets = {
            "datetime": forms.DateTimeInput(attrs={"type": "datetime-local"}),
        }


class TransferForm(BaseModelForm):
    class Meta:
        model = Transfer
        fields = ["method", "value"]


class UserSettingsForm(BaseModelForm):
    class Meta:
        model = User
        fields = ["email", "username", "tz", "hc"]
