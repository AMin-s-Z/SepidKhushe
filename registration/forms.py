from django import forms
from django.utils.translation import gettext_lazy as _
from .models import Registration


class RegistrationForm(forms.ModelForm):
    """Form for course registration"""
    
    class Meta:
        model = Registration
        fields = ['name', 'phone', 'payment_type']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 mt-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-600',
                'placeholder': _('نام و نام خانوادگی خود را وارد کنید'),
            }),
            'phone': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 mt-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-600',
                'placeholder': _('شماره تماس خود را وارد کنید'),
                'dir': 'ltr',
            }),
            'payment_type': forms.RadioSelect(attrs={
                'class': 'form-radio h-5 w-5 text-indigo-600',
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].label_attrs = {'class': 'block text-sm font-medium text-gray-700'}
            
