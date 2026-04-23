from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Sum, Count
from django.utils import timezone
from django.http import JsonResponse
from datetime import timedelta
from sales.models import Sale, SaleItem
from products.models import Product, StockHistory
from customers.models import Customer
from reports.models import Credit
from django.contrib.auth import get_user_model

User = get_user_model()


@login_required
def user_list(request):
    status_filter = request.GET.get('status', 'registered')
    
    if status_filter == 'archived':
        users = User.objects.filter(is_active=False)
    else:
        users = User.objects.filter(is_active=True)
    
    search = request.GET.get('search')
    if search:
        users = users.filter(username__icontains=search) | users.filter(email__icontains=search)
    
    users = users.order_by('-date_joined')
    paginator = Paginator(users, 20)
    page = request.GET.get('page')
    users = paginator.get_page(page)
    return render(request, 'users/user_list.html', {
        'users': users,
        'status_filter': status_filter
    })


@login_required
def user_create(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        role = request.POST.get('role', 'staff')
        
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists')
        else:
            User.objects.create_user(username=username, email=email, password=password, role=role)
            messages.success(request, 'User created successfully')
            return redirect('users:user_list')
    return render(request, 'users/user_form.html')


@login_required
def user_edit(request, pk):
    user = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        user.email = request.POST.get('email')
        user.role = request.POST.get('role', user.role)
        if request.POST.get('password'):
            user.set_password(request.POST.get('password'))
        user.save()
        messages.success(request, 'User updated')
        return redirect('users:user_list')
    return render(request, 'users/user_form.html', {'user_obj': user})


@login_required
def user_delete(request, pk):
    user = get_object_or_404(User, pk=pk)
    user.delete()
    messages.success(request, 'User deleted')
    return redirect('users:user_list')


@login_required
def user_toggle_archive(request, pk):
    user = get_object_or_404(User, pk=pk)
    user.is_active = not user.is_active
    user.save()
    status = 'archived' if not user.is_active else 'restored'
    messages.success(request, f'User {status} successfully')
    return redirect('users:user_list')


def login_view(request):
    if request.user.is_authenticated:
        if request.user.is_superuser or request.user.role == 'admin':
            return redirect('/reports/summary/')
        elif request.user.is_staff:
            return redirect('/sales/sale_list/?date=today')
        else:
            return redirect('/sales/pos/')
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            if user.is_superuser or user.role == 'admin':
                return redirect('/reports/summary/')
            elif user.is_staff:
                return redirect('/sales/sale_list/?date=today')
            else:
                return redirect('/sales/pos/')
        messages.error(request, 'Invalid credentials')
    return render(request, 'accounts/login.html')

def register_view(request):
    if request.user.is_authenticated:
        return redirect('/reports/summary/')
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        first_name = request.POST.get('first_name', '')
        last_name = request.POST.get('last_name', '')
        
        if password != confirm_password:
            messages.error(request, 'Passwords do not match')
            return render(request, 'accounts/register.html')
        
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists')
            return render(request, 'accounts/register.html')
        
        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already exists')
            return render(request, 'accounts/register.html')
        
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            role='staff'
        )
        messages.success(request, 'Account created successfully! Please login.')
        return redirect('login')
    return render(request, 'accounts/register.html')


def logout_view(request):
    logout(request)
    return redirect('login')


@login_required
def dashboard(request):
    is_admin_user = request.user.is_superuser or request.user.role == 'admin'
    is_staff_user = request.user.is_staff
    
    # Regular staff (non-admin) - redirect to limited view
    if not is_admin_user and not is_staff_user:
        return redirect('reports:expense_list')  # Will show credits
    
    today = timezone.now().date()
    
    total_sales_today = Sale.objects.filter(created_at__date=today, status='completed').count()
    total_sales_count = Sale.objects.filter(status='completed').count()
    revenue_today = Sale.objects.filter(created_at__date=today, status='completed').aggregate(
        total=Sum('total_amount')
    )['total'] or 0
    
    low_stock_count = Product.objects.filter(stock_quantity__lte=10, is_active=True).count()
    total_products = Product.objects.filter(is_active=True).count()
    total_customers = Customer.objects.count()
    total_stock = Product.objects.filter(is_active=True).aggregate(total=Sum('stock_quantity'))['total'] or 0
    
    week_ago = today - timedelta(days=7)
    revenue_week = Sale.objects.filter(created_at__date__gte=week_ago, status='completed').aggregate(
        total=Sum('total_amount')
    )['total'] or 0
    
    credits_today = Credit.objects.filter(date=today).aggregate(total=Sum('amount'))['total'] or 0
    total_expenses = Credit.objects.aggregate(total=Sum('amount'))['total'] or 0
    outstanding_balance = Credit.objects.filter(status__in=['pending', 'overdue']).aggregate(
        total=Sum('amount')
    )['total'] or 0
    outstanding_balance = outstanding_balance or 0
    
    top_products = SaleItem.objects.all().values(
        'product__id', 'product__name'
    ).annotate(
        total_sold=Sum('quantity'),
        total_revenue=Sum('total_price')
    ).order_by('-total_sold')[:5]
    
    recent_sales = Sale.objects.filter(status='completed').order_by('-created_at')[:5]
    
    stock_per_product = Product.objects.filter(is_active=True).order_by('-stock_quantity')[:15]
    
    sales_data = []
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        day_sales = Sale.objects.filter(created_at__date=day, status='completed').aggregate(
            total=Sum('total_amount')
        )['total'] or 0
        sales_data.append({
            'date': day.strftime('%Y-%m-%d'),
            'label': day.strftime('%b %d'),
            'amount': float(day_sales)
        })
    
    context = {
        'total_sales_today': total_sales_today,
        'total_sales_count': total_sales_count,
        'revenue_today': revenue_today,
        'revenue_week': revenue_week,
        'low_stock_count': low_stock_count,
        'total_products': total_products,
        'total_customers': total_customers,
        'total_stock': total_stock,
        'credits_today': credits_today,
        'total_expenses': total_expenses,
        'outstanding_balance': outstanding_balance,
        'top_products': top_products,
        'recent_sales': recent_sales,
        'stock_per_product': stock_per_product,
        'sales_data': sales_data,
    }
    return render(request, 'dashboard/index.html', context)