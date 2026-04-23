from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from django.utils import timezone
from datetime import datetime
from .models import Sale, SaleItem
from products.models import Product, StockHistory
from .serializers import SaleSerializer, SaleItemSerializer


class SaleViewSet(viewsets.ModelViewSet):
    queryset = Sale.objects.all()
    serializer_class = SaleSerializer
    permission_classes = [IsAuthenticated]
    
    def generate_invoice_number(self):
        today = datetime.now().strftime('%Y%m%d')
        last_sale = Sale.objects.filter(invoice_number__startswith=f'INV-{today}').order_by('-invoice_number').first()
        if last_sale:
            last_num = int(last_sale.invoice_number.split('-')[-1])
            return f'INV-{today}-{str(last_num + 1).zfill(4)}'
        return f'INV-{today}-0001'
    
    @transaction.atomic
    def create(self, request, *args, **kwargs):
        data = request.data
        items_data = data.get('items', [])
        if not items_data:
            return Response({'error': 'No items provided'}, status=status.HTTP_400_BAD_REQUEST)
        
        subtotal = 0
        sale_items = []
        
        for item in items_data:
            product = Product.objects.get(pk=item['product'])
            quantity = item['quantity']
            unit_price = item.get('unit_price', product.selling_price)
            
            if product.stock_quantity < quantity:
                return Response({'error': f'Insufficient stock for {product.name}'}, status=status.HTTP_400_BAD_REQUEST)
            
            total_price = unit_price * quantity
            subtotal += total_price
            sale_items.append({
                'product': product,
                'quantity': quantity,
                'unit_price': unit_price,
                'total_price': total_price
            })
        
        discount = data.get('discount_amount', 0)
        amount_paid = data.get('amount_paid', 0)
        total = subtotal - discount
        
        if amount_paid < total:
            return Response({'error': 'Insufficient payment'}, status=status.HTTP_400_BAD_REQUEST)
        
        change = amount_paid - total
        
        payment_method = data.get('payment_method', 'cash')
        
        sale = Sale.objects.create(
            invoice_number=self.generate_invoice_number(),
            customer_id=data.get('customer'),
            subtotal=subtotal,
            discount_amount=discount,
            total_amount=total,
            amount_paid=amount_paid,
            change_given=change,
            notes=data.get('notes', ''),
            created_by=request.user,
            payment_method=payment_method
        )
        
        for item in sale_items:
            SaleItem.objects.create(
                sale=sale,
                product=item['product'],
                quantity=item['quantity'],
                unit_price=item['unit_price'],
                total_price=item['total_price']
            )
            product = item['product']
            product.stock_quantity -= item['quantity']
            product.save()
            StockHistory.objects.create(
                product=product,
                action='sale',
                quantity=-item['quantity'],
                reference=sale.invoice_number,
                created_by=request.user
            )
        
        serializer = self.get_serializer(sale)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['get'])
    def today(self, request):
        today = timezone.now().date()
        sales = Sale.objects.filter(created_at__date=today, status='completed')
        total_revenue = sum(s.total_amount for s in sales)
        data = {
            'count': sales.count(),
            'total_revenue': total_revenue,
            'sales': SaleSerializer(sales, many=True).data
        }
        return Response(data)