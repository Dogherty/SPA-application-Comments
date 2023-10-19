from django import forms
from .models import Comment
from captcha.fields import CaptchaField

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['user_name', 'email', 'home_page', 'captcha', 'text']

    user_name = forms.CharField(label='User Name', max_length=100, widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(label='E-mail', widget=forms.EmailInput(attrs={'class': 'form-control'}))
    home_page = forms.URLField(label='Home Page', required=False, widget=forms.URLInput(attrs={'class': 'form-control'}))
    captcha = CaptchaField(required=False)
    text = forms.CharField(label='Text', widget=forms.Textarea(attrs={'class': 'form-control'}))
    image = forms.ImageField(label='Upload Image', required=False,
                             widget=forms.ClearableFileInput(attrs={'class': 'custom-file-input'}))
    file = forms.FileField(label='Upload Text File', required=False,
                           widget=forms.ClearableFileInput(attrs={'class': 'custom-file-input'}))
