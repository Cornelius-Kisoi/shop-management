from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, Submit, Field
from .models import Product, Category, Supplier


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = '__all__'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_class = 'row g-3'
        self.helper.layout = Layout(
            Row(
                Column('name', css_class='col-md-6'),
                Column('sku', css_class='col-md-6'),
            ),
            Row(
                Column('barcode', css_class='col-md-6'),
                Column('category', css_class='col-md-6'),
            ),
            Row(
                Column('supplier', css_class='col-md-6'),
                Column('description', css_class='col-md-6'),
            ),
            Row(
                Column('cost_price', css_class='col-md-3'),
                Column('selling_price', css_class='col-md-3'),
                Column('stock_quantity', css_class='col-md-3'),
                Column('low_stock_threshold', css_class='col-md-3'),
            ),
            Row(
                Column('is_active', css_class='col-md-12'),
            ),
            Submit('submit', 'Save Product', css_class='btn-primary mt-3')
        )
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = '__all__'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            'name',
            'description',
            Submit('submit', 'Save Category', css_class='btn-primary mt-3')
        )
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})


class SupplierForm(forms.ModelForm):
    class Meta:
        model = Supplier
        fields = '__all__'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Row(
                Column('name', css_class='col-md-6'),
                Column('contact_person', css_class='col-md-6'),
            ),
            Row(
                Column('email', css_class='col-md-6'),
                Column('phone', css_class='col-md-6'),
            ),
            'address',
            Submit('submit', 'Save Supplier', css_class='btn-primary mt-3')
        )
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})