from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.conf import settings
from django.contrib.staticfiles import finders
from django.db import transaction
from django.db.models import Sum, F, DecimalField
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal
from reports.models import Credit, CreditCategory
from customers.models import Customer
from sales.models import Sale
from products.models import Product
from xhtml2pdf import pisa
import io
import os
from django.contrib import messages


def link_callback(uri, rel):
    if uri.startswith(settings.STATIC_URL):
        path = uri.replace(settings.STATIC_URL, '')
        result = finders.find(path)
        if result:
            return result if isinstance(result, str) else result[0]
    if uri.startswith(settings.MEDIA_URL):
        path = uri.replace(settings.MEDIA_URL, '')
        return os.path.join(settings.MEDIA_ROOT, path)
    if uri.startswith('http://') or uri.startswith('https://'):
        return uri
    return os.path.join(settings.STATIC_ROOT, uri)


def convert_html_to_pdf(source_html):
    result = io.BytesIO()
    pdf = pisa.CreatePDF(source_html, dest=result, link_callback=link_callback)
    if pdf.err:
        return None
    return result.getvalue()


def is_admin(user):
    return user.is_superuser or user.role == 'admin'


def is_staff_user(user):
    return user.is_superuser or user.role == 'admin' or user.is_staff


@login_required
def expense_list(request):
    credits = Credit.objects.select_related('category', 'customer', 'created_by').order_by('-date')
    categories = CreditCategory.objects.all()
    
    search = request.GET.get('search')
    if search:
        credits = credits.filter(description__icontains=search) | credits.filter(customer__name__icontains=search)
    
    status_filter = request.GET.get('status')
    if status_filter:
        credits = credits.filter(status=status_filter)
    
    category_filter = request.GET.get('category')
    if category_filter:
        credits = credits.filter(category_id=category_filter)
    
    paginator = Paginator(credits, 20)
    page = request.GET.get('page')
    credits = paginator.get_page(page)
    
    return render(request, 'reports/credit_list.html', {
        'credits': credits,
        'status_filter': status_filter,
        'category_filter': category_filter,
        'categories': categories,
    })


@login_required
def customer_debts(request):
    customers = Customer.objects.filter(credits__status__in=['pending', 'overdue']).annotate(
        total_owed=Sum(
            F('credits__amount') - F('credits__amount_paid'),
            output_field=DecimalField()
        )
    ).filter(total_owed__gt=0).order_by('-total_owed').distinct()

    selected_customer = None
    pending_credits = []
    selected_total = Decimal('0')
    customer_id = request.GET.get('customer_id')

    if customer_id:
        selected_customer = get_object_or_404(Customer, pk=customer_id)
        pending_credits = selected_customer.credits.filter(status__in=['pending', 'overdue']).order_by('date')
        selected_total = pending_credits.aggregate(
            total=Sum(F('amount') - F('amount_paid'), output_field=DecimalField())
        )['total'] or Decimal('0')

    return render(request, 'reports/customer_debts.html', {
        'customers': customers,
        'selected_customer': selected_customer,
        'pending_credits': pending_credits,
        'selected_total': selected_total,
    })


@login_required
@transaction.atomic
def record_customer_payment(request):
    if request.method != 'POST':
        return redirect('reports:customer_debts')

    customer_id = request.POST.get('customer_id')
    payment_amount = request.POST.get('payment_amount', '0')
    try:
        payment_amount = Decimal(payment_amount)
    except Exception:
        messages.error(request, 'Enter a valid payment amount.')
        return redirect('reports:customer_debts')

    if payment_amount <= 0:
        messages.error(request, 'Enter a payment amount greater than zero.')
        return redirect('reports:customer_debts')

    customer = get_object_or_404(Customer, pk=customer_id)
    credits = customer.credits.filter(status__in=['pending', 'overdue']).order_by('date')
    total_outstanding = sum((credit.outstanding_balance for credit in credits), Decimal('0'))

    if payment_amount > total_outstanding:
        messages.error(request, 'Payment exceeds outstanding balance.')
        return redirect('reports:customer_debts')

    remaining = payment_amount
    for credit in credits:
        if remaining <= 0:
            break
        outstanding = credit.outstanding_balance
        if outstanding <= 0:
            continue
        applied = min(outstanding, remaining)
        credit.amount_paid += applied
        if credit.amount_paid >= credit.amount:
            credit.status = 'paid'
        credit.save()

        if credit.sale:
            total_sale_paid = credit.sale.credits.aggregate(total=Sum('amount_paid'))['total'] or Decimal('0')
            credit.sale.amount_paid = total_sale_paid
            if not credit.sale.credits.filter(status__in=['pending', 'overdue']).exists():
                credit.sale.payment_status = 'paid'
                credit.sale.status = 'completed'
            credit.sale.save(update_fields=['amount_paid', 'payment_status', 'status'])

        remaining -= applied

    if customer.current_credit:
        customer.current_credit = max(Decimal('0'), customer.current_credit - payment_amount)
        customer.save()

    messages.success(request, f'Payment of KSh {payment_amount:,.2f} applied to pending credits.')
    return redirect(f"{reverse('reports:customer_debts')}?customer_id={customer.id}")


@login_required
def credit_receipt(request, pk):
    credit = get_object_or_404(Credit, pk=pk)
    previous_credits = Credit.objects.filter(customer=credit.customer, date__lt=credit.date).order_by('-date')
    previous_balance = previous_credits.aggregate(
        total=Sum(F('amount') - F('amount_paid'), output_field=DecimalField())
    )['total'] or Decimal('0')
    previous_balance_date = previous_credits.values_list('date', flat=True).first() or credit.date

    if request.GET.get('download'):
        html_string = render_to_string('reports/credit_receipt.html', {
            'credit': credit,
            'previous_balance': previous_balance,
            'previous_balance_date': previous_balance_date,
        }, request=request)
        pdf = convert_html_to_pdf(html_string)
        if pdf is None:
            return HttpResponse('PDF generation failed', status=500)
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="credit-receipt-{credit.id}.pdf"'
        return response

    return render(request, 'reports/credit_receipt.html', {
        'credit': credit,
        'previous_balance': previous_balance,
        'previous_balance_date': previous_balance_date,
    })


@login_required
def debts_receipt(request):
    if request.method != 'POST':
        return redirect('reports:customer_debts')

    selected_ids = request.POST.getlist('selected_credits')
    action = request.POST.get('action')
    if not selected_ids:
        messages.warning(request, 'Select at least one credit entry to print or download.')
        return redirect('reports:customer_debts')

    credits = Credit.objects.filter(pk__in=selected_ids).select_related('customer', 'sale').order_by('date')
    if not credits.exists():
        messages.error(request, 'No matching debt records found.')
        return redirect('reports:customer_debts')

    customer = credits[0].customer
    if credits.filter(customer_id=customer.id).count() != credits.count():
        messages.error(request, 'Selected credits must belong to the same customer.')
        return redirect('reports:customer_debts')

    total_amount = credits.aggregate(total=Sum('amount'))['total'] or Decimal('0')
    total_paid = credits.aggregate(total=Sum('amount_paid'))['total'] or Decimal('0')
    total_outstanding = sum((c.outstanding_balance for c in credits), Decimal('0'))

    if action == 'download':
        html_string = render_to_string('reports/multi_credit_receipt.html', {
            'credits': credits,
            'customer': customer,
            'total_amount': total_amount,
            'total_paid': total_paid,
            'total_outstanding': total_outstanding,
        }, request=request)
        pdf = convert_html_to_pdf(html_string)
        if pdf is None:
            return HttpResponse('PDF generation failed', status=500)
        filename = f"debt-receipt-{customer.name.replace(' ', '_')}.pdf"
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response

    return render(request, 'reports/multi_credit_receipt.html', {
        'credits': credits,
        'customer': customer,
        'total_amount': total_amount,
        'total_paid': total_paid,
        'total_outstanding': total_outstanding,
    })


@login_required
def expense_create(request):
    if not is_admin(request.user):
        messages.warning(request, 'You do not have permission to add credits.')
        return redirect('reports:expense_list')
    
    categories = CreditCategory.objects.all()
    from customers.models import Customer
    customers = Customer.objects.all()
    
    if request.method == 'POST':
        category_id = request.POST.get('category')
        customer_id = request.POST.get('customer')
        amount = request.POST.get('amount')
        description = request.POST.get('description')
        date = request.POST.get('date')
        due_date = request.POST.get('due_date')
        
        Credit.objects.create(
            category_id=category_id if category_id else None,
            customer_id=customer_id,
            amount=amount, description=description,
            date=date, due_date=due_date,
            created_by=request.user
        )
        messages.success(request, 'Credit added successfully')
        return redirect('reports:expense_list')
    return render(request, 'reports/credit_form.html', {'categories': categories, 'customers': customers})


@login_required
def expense_category_list(request):
    if not is_admin(request.user):
        messages.warning(request, 'Only admins can manage credit categories.')
        return redirect('reports:expense_list')
    
    categories = CreditCategory.objects.all()
    return render(request, 'reports/category_list.html', {'categories': categories})


@login_required
def expense_category_create(request):
    if request.user.role != 'admin':
        messages.warning(request, 'Only admins can manage credit categories.')
        return redirect('reports:expense_list')
    
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        CreditCategory.objects.create(name=name, description=description)
        messages.success(request, 'Category created successfully')
        return redirect('reports:category_list')
    return render(request, 'reports/category_form.html')


@login_required
def summary(request):
    if not (request.user.is_superuser or request.user.role == 'admin'):
        messages.warning(request, 'Only admins can view the summary.')
        return redirect('reports:expense_list')

    period = request.GET.get('period', 'week')
    today = timezone.now().date()
    
    if period == 'day':
        start = today
    elif period == 'week':
        start = today - timedelta(days=7)
    elif period == 'month':
        start = today - timedelta(days=30)
    else:
        start = today - timedelta(days=30)
    
    sales = Sale.objects.filter(created_at__date__gte=start, status='completed')
    total_revenue = sales.aggregate(total=Sum('total_amount'))['total'] or 0
    total_sales_count = sales.count()
    
    credits = Credit.objects.filter(date__gte=start)
    total_credits = credits.aggregate(total=Sum('amount'))['total'] or 0
    credits_all = Credit.objects.all()
    total_credits_all = credits_all.aggregate(total=Sum('amount'))['total'] or 0
    outstanding = Credit.objects.filter(status__in=['pending', 'overdue']).aggregate(total=Sum('amount'))['total'] or 0
    outstanding = float(outstanding or 0) if outstanding else 0
    net_profit = float(total_revenue or 0) - float(total_credits_all or 0)
    
    total_stock_value = Product.objects.filter(is_active=True).aggregate(
        total=Sum('stock_quantity')
    )['total'] or 0
    
    low_stock = Product.objects.filter(is_active=True, stock_quantity__lte=10)
    low_stock_products = Product.objects.filter(is_active=True).order_by('stock_quantity')[:10]
    
    daily_sales = sales.extra(select={'day': "date(created_at)"}).values('day').annotate(total=Sum('total_amount'))
    daily_credits = credits.extra(select={'day': 'date'}).values('day').annotate(total=Sum('amount'))
    
    context = {
        'period': period,
        'total_revenue': total_revenue,
        'total_credits': total_credits,
        'outstanding_balance': outstanding or 0,
        'total_sales_count': total_sales_count,
        'total_stock_value': total_stock_value or 0,
        'low_stock_count': low_stock.count(),
        'net_profit': net_profit or 0,
        'daily_sales': list(daily_sales),
        'daily_credits': list(daily_credits),
        'is_admin': is_admin(request.user),
    }
    return render(request, 'reports/summary.html', context)