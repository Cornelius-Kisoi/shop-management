from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.http import JsonResponse, HttpResponse
from django.template.loader import render_to_string
from django.conf import settings
from django.contrib.staticfiles import finders
from sales.models import Sale, SaleItem
from products.models import Product, StockHistory
from customers.models import Customer
from reports.models import Credit
from django.db import transaction
from django.utils import timezone
from datetime import datetime
from xhtml2pdf import pisa
import io
import os


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


@login_required
def sale_list(request):
    # Regular staff can only see today's sales, not full history
    if not (request.user.is_superuser or request.user.role == 'admin' or request.user.is_staff):
        today = timezone.now().date()
        date_filter = request.GET.get('date', 'today')
        if date_filter == 'today':
            sales = Sale.objects.filter(created_at__date=today).select_related('customer', 'created_by').order_by('-created_at')
        else:
            sales = Sale.objects.none()  # Empty
    else:
        sales = Sale.objects.select_related('customer', 'created_by').order_by('-created_at')
        date_filter = request.GET.get('date')
        if date_filter == 'today':
            today = timezone.now().date()
            sales = sales.filter(created_at__date=today)
    
    search = request.GET.get('search')
    if search:
        sales = sales.filter(invoice_number__icontains=search) | sales.filter(customer__name__icontains=search)
    
    status_filter = request.GET.get('status')
    if status_filter:
        sales = sales.filter(status=status_filter)
    
    payment_filter = request.GET.get('payment')
    if payment_filter:
        sales = sales.filter(payment_status=payment_filter)
    
    paginator = Paginator(sales, 20)
    page = request.GET.get('page')
    sales = paginator.get_page(page)
    return render(request, 'sales/sale_list.html', {
        'sales': sales,
        'status_filter': status_filter,
        'payment_filter': payment_filter
    })


@login_required
def pos(request):
    """Point of Sale - Main POS interface"""
    products = Product.objects.filter(is_active=True, stock_quantity__gt=0).select_related('category')
    categories = products.exclude(category__name__isnull=True).values_list('category__name', flat=True)
    categories = sorted(set(categories))
    customers = Customer.objects.all()[:10]
    
    return render(request, 'sales/pos.html', {
        'products': products,
        'categories': categories,
        'customers': customers,
    })


@login_required
def pos_search_products(request):
    """API to search products for POS"""
    query = request.GET.get('q', '')
    category = request.GET.get('category', '')
    
    products = Product.objects.filter(is_active=True, stock_quantity__gt=0).select_related('category')
    
    if query:
        products = products.filter(name__icontains=query) | products.filter(sku__icontains=query) | products.filter(barcode__icontains=query)
    
    if category:
        products = products.filter(category__name=category)
    
    products = products[:20]
    
    data = [{
        'id': p.id,
        'name': p.name,
        'sku': p.sku,
        'barcode': p.barcode,
        'price': float(p.selling_price),
        'stock': p.stock_quantity,
        'category': p.category.name if p.category else 'Uncategorized'
    } for p in products]
    
    return JsonResponse(data, safe=False)


@login_required
@transaction.atomic
def pos_process_sale(request):
    """Process POS sale"""
    try:
        data = request.POST
        items = data.get('items', '')
        amount_paid = float(data.get('amount_paid', 0) or 0)
        customer_id = data.get('customer_id', '')
        payment_method = data.get('payment_method', 'cash')
        notes = data.get('notes', '')
        
        if not items:
            return JsonResponse({'success': False, 'error': 'No items selected'})
        
        import json
        items_list = json.loads(items)
        
        if not items_list:
            return JsonResponse({'success': False, 'error': 'No items in cart'})
        
        today = datetime.now().strftime('%Y%m%d')
        last_sale = Sale.objects.filter(invoice_number__startswith=f'INV-{today}').order_by('-invoice_number').first()
        if last_sale:
            last_num = int(last_sale.invoice_number.split('-')[-1])
            invoice_number = f'INV-{today}-{str(last_num + 1).zfill(4)}'
        else:
            invoice_number = f'INV-{today}-0001'
        
        subtotal = 0
        sale_items_data = []
        
        for item in items_list:
            product = Product.objects.select_for_update().get(pk=item['product'])
            qty = int(item['quantity'])
            unit_price = float(item.get('unit_price', product.selling_price))
            
            if product.stock_quantity < qty:
                return JsonResponse({'success': False, 'error': f'Insufficient stock for {product.name}. Available: {product.stock_quantity}'})
            
            total_price = unit_price * qty
            subtotal += total_price
            sale_items_data.append({
                'product': product,
                'quantity': qty,
                'unit_price': unit_price,
                'total_price': total_price
            })
        
        total = float(subtotal)
        
        from decimal import Decimal
        
        # Handle credit sale
        if payment_method == 'credit':
            if not customer_id:
                return JsonResponse({'success': False, 'error': 'Please select a customer for credit sale'})
            
            amount_paid = 0
            change = 0
            sale_status = 'pending'
            payment_status = 'credit'
        else:
            amount_paid = float(amount_paid)
            if amount_paid < total:
                return JsonResponse({'success': False, 'error': f'Insufficient payment. Total: KSh {total:,.2f}'})
            change = amount_paid - total
            sale_status = 'completed'
            payment_status = 'paid'
        
        sale = Sale.objects.create(
            invoice_number=invoice_number,
            customer_id=customer_id if customer_id else None,
            subtotal=Decimal(str(subtotal)),
            total_amount=Decimal(str(total)),
            amount_paid=Decimal(str(amount_paid)),
            change_given=Decimal(str(change)),
            notes=notes,
            created_by=request.user,
            status=sale_status,
            payment_status=payment_status,
            payment_method=payment_method
        )

        if payment_method == 'credit':
            Credit.objects.create(
                customer_id=customer_id,
                sale=sale,
                amount=Decimal(str(total)),
                amount_paid=Decimal('0'),
                description=f'Credit sale: {invoice_number}',
                date=datetime.now().date(),
                status='pending',
                created_by=request.user
            )
        
        # Create sale items and update stock
        for item in sale_items_data:
            product = item['product']
            qty = item['quantity']
            
            SaleItem.objects.create(
                sale=sale,
                product=product,
                quantity=qty,
                unit_price=Decimal(str(item['unit_price'])),
                total_price=Decimal(str(item['total_price']))
            )
            
            # Update stock
            product.stock_quantity -= qty
            product.save()
            
            # Record stock history
            StockHistory.objects.create(
                product=product,
                action='sale',
                quantity=-qty,
                reference=invoice_number,
                created_by=request.user
            )
        
        return JsonResponse({
            'success': True,
            'sale_id': sale.id,
            'invoice_number': invoice_number,
            'total': total,
            'amount_paid': amount_paid,
            'change': change,
            'items': len(sale_items_data)
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
def sale_receipt(request, pk):
    """Generate sale receipt"""
    sale = get_object_or_404(Sale, pk=pk)
    if request.GET.get('download'):
        html_string = render_to_string('sales/receipt.html', {'sale': sale}, request=request)
        pdf = convert_html_to_pdf(html_string)
        if pdf is None:
            return HttpResponse('PDF generation failed', status=500)
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="sale-receipt-{sale.invoice_number}.pdf"'
        return response

    return render(request, 'sales/receipt.html', {'sale': sale})


@login_required
@transaction.atomic
def reset_sales_and_credits(request):
    if not (request.user.is_superuser or request.user.role == 'admin'):
        messages.warning(request, 'You do not have permission to reset sales and credits.')
        return redirect('sales:sale_list')

    if request.method == 'POST':
        Credit.objects.all().delete()
        Sale.objects.all().delete()
        messages.success(request, 'All sales and credits have been cleared. You can now enter fresh demo data.')
        return redirect('sales:sale_list')

    return render(request, 'sales/reset_data_confirm.html')


@login_required
def sale_create(request):
    """Legacy sale create - redirect to POS"""
    return redirect('sales:pos')


@login_required
def sale_detail(request, pk):
    sale = get_object_or_404(Sale, pk=pk)
    credit_receipt_url = None
    if sale.payment_status == 'credit':
        credit = Credit.objects.filter(sale=sale).order_by('-date').first()
        if credit:
            from django.urls import reverse
            credit_receipt_url = reverse('reports:credit_receipt', args=[credit.id])
    return render(request, 'sales/sale_detail.html', {
        'sale': sale,
        'credit_receipt_url': credit_receipt_url,
    })


@login_required
def receipt_list(request):
    """List all sales to send receipts"""
    sales = Sale.objects.select_related('customer', 'created_by').order_by('-created_at')
    
    search = request.GET.get('search')
    if search:
        sales = sales.filter(invoice_number__icontains=search) | sales.filter(customer__name__icontains=search)
    
    status_filter = request.GET.get('status')
    if status_filter:
        sales = sales.filter(status=status_filter)
    
    paginator = Paginator(sales, 25)
    page = request.GET.get('page')
    sales = paginator.get_page(page)
    
    return render(request, 'sales/receipt_list.html', {'sales': sales})


@login_required
def send_receipt(request, pk):
    """Send receipt via WhatsApp or Email"""
    sale = get_object_or_404(Sale, pk=pk)
    method = request.GET.get('method', 'whatsapp')
    phone = request.GET.get('phone', '')
    
    if not sale.customer and not phone:
        messages.error(request, 'No customer phone number available')
        return redirect('sales:receipts')
    
    customer_phone = phone or (sale.customer.phone if sale.customer else '')
    
    if method == 'whatsapp':
        receipt_text = f"*{sale.invoice_number}*\n\n"
        receipt_text += f"Date: {sale.created_at.strftime('%d %b %Y, %H:%M')}\n\n"
        receipt_text += f"Items:\n"
        for item in sale.items.all():
            receipt_text += f"- {item.product.name} x{item.quantity} = KSh {item.total_price}\n"
        receipt_text += f"\nTotal: KSh {sale.total_amount}\n"
        receipt_text += f"Paid: KSh {sale.amount_paid}\n"
        receipt_text += f"Change: KSh {sale.change_given}\n\n"
        receipt_text += f"Thank you for shopping with EXTREME TECH!"
        
        wa_msg = receipt_text.replace('\n', '%0A').replace('*', '%2A')
        wa_url = f"https://wa.me/{customer_phone.replace('+', '').replace(' ', '')}?text={wa_msg}"
        
        return redirect(wa_url)
    
    elif method == 'email':
        from django.core.mail import send_mail
        if not sale.customer or not sale.customer.email:
            messages.error(request, 'No customer email available')
            return redirect('sales:receipts')
        
        subject = f'Receipt {sale.invoice_number} - EXTREME TECH'
        message = f"Thank you for your purchase!\n\nInvoice: {sale.invoice_number}\nTotal: KSh {sale.total_amount}"
        
        try:
            send_mail(subject, message, 'noreply@extremetech.com', [sale.customer.email])
            messages.success(request, f'Receipt sent to {sale.customer.email}')
        except Exception as e:
            messages.error(request, f'Failed to send email: {str(e)}')
        
        return redirect('sales:receipts')
    
    return redirect('sales:receipts')