from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from customers.models import Customer


def is_admin(user):
    return user.is_superuser or user.role == 'admin'


@login_required
def customer_list(request):
    customers = Customer.objects.order_by('-created_at')
    search = request.GET.get('search')
    if search:
        customers = customers.filter(name__icontains=search) | customers.filter(phone__icontains=search)
    paginator = Paginator(customers, 20)
    page = request.GET.get('page')
    customers = paginator.get_page(page)
    return render(request, 'customers/customer_list.html', {'customers': customers})


@login_required
def customer_create(request):
    if not (request.user.is_superuser or request.user.role == 'admin'):
        messages.warning(request, 'You do not have permission to add customers.')
        return redirect('customers:customer_list')
    
    if request.method == 'POST':
        name = request.POST.get('name')
        if not name:
            messages.error(request, 'Customer name is required.')
            return redirect('customers:customer_create')
        
        email = request.POST.get('email') or None
        phone = request.POST.get('phone') or None
        address = request.POST.get('address') or None
        credit_limit = request.POST.get('credit_limit', 0) or 0
        
        Customer.objects.create(
            name=name, email=email, phone=phone,
            address=address, credit_limit=credit_limit,
            created_by=request.user
        )
        messages.success(request, 'Customer created successfully')
        return redirect('customers:customer_list')
    return render(request, 'customers/customer_form.html')


@login_required
def customer_edit(request, pk):
    if not (request.user.is_superuser or request.user.role == 'admin'):
        messages.warning(request, 'You do not have permission to edit customers.')
        return redirect('customers:customer_list')
    
    customer = get_object_or_404(Customer, pk=pk)
    if request.method == 'POST':
        customer.name = request.POST.get('name')
        if not customer.name:
            messages.error(request, 'Customer name is required.')
            return render(request, 'customers/customer_form.html', {'customer': customer})
        customer.email = request.POST.get('email') or None
        customer.phone = request.POST.get('phone') or None
        customer.address = request.POST.get('address') or None
        customer.credit_limit = request.POST.get('credit_limit', 0) or 0
        customer.save()
        messages.success(request, 'Customer updated successfully')
        return redirect('customers:customer_list')
    return render(request, 'customers/customer_form.html', {'customer': customer})


@login_required
def customer_delete(request, pk):
    if not (request.user.is_superuser or request.user.role == 'admin'):
        messages.warning(request, 'You do not have permission to delete customers.')
        return redirect('customers:customer_list')
    
    customer = get_object_or_404(Customer, pk=pk)
    customer.delete()
    messages.success(request, 'Customer deleted successfully')
    return redirect('customers:customer_list')