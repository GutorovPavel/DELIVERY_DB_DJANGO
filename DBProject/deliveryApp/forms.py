from django import forms


class AddClientForm(forms.Form):
    first_name = forms.CharField(max_length=100)
    last_name = forms.CharField(max_length=100)
    email = forms.EmailField(max_length=100)
    phone = forms.CharField(max_length=13)
    address = forms.CharField(max_length=100)


class EditClientForm(forms.Form):
    first_name = forms.CharField(max_length=100)
    last_name = forms.CharField(max_length=100)
    email = forms.EmailField(max_length=100)
    phone = forms.CharField(max_length=13)
    # address = forms.CharField(max_length=100)


class LoginClientForm(forms.Form):
    phone = forms.CharField(max_length=13)
