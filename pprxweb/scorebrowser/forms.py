from django import forms
from django.contrib.auth.forms import SetPasswordForm, UserCreationForm
from django.contrib.auth.models import User as DjangoUser


class UserRegistrationForm(UserCreationForm):
	email = forms.EmailField(help_text='Email address for password resets', required=True)

	class Meta:
		model = DjangoUser
		fields = ['username', 'email', 'password1', 'password2']

	def clean_email(self):
		email = self.cleaned_data['email']
		if DjangoUser.objects.filter(email=email).exists():
			raise forms.ValidationError("That email is already registered!")
		return self.cleaned_data['email']

	def save(self, commit=True):
		user = super(UserRegistrationForm, self).save(commit=False)
		user.email = self.cleaned_data['email']
		if commit:
			user.save()
		return user


class UpdateEmailForm(forms.ModelForm):
	email = forms.EmailField(help_text='Email address for password resets', required=True)

	class Meta:
		model = DjangoUser
		fields = ['email']


class SetPasswordForm(SetPasswordForm):
	class Meta:
		model = DjangoUser
		fields = ['new_password1', 'new_password2']
