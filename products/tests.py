from django.test import TestCase
from products.models import Product, Category, Supplier


class ProductModelTest(TestCase):
    def test_product_creation(self):
        category = Category.objects.create(name='Test Category')
        supplier = Supplier.objects.create(name='Test Supplier')
        
        product = Product.objects.create(
            name='Test Product',
            sku='TEST-001',
            category=category,
            supplier=supplier,
            selling_price=100.00,
            stock_quantity=10
        )
        
        self.assertEqual(product.name, 'Test Product')
        self.assertEqual(product.sku, 'TEST-001')
        self.assertEqual(product.selling_price, 100.00)
        self.assertEqual(product.stock_quantity, 10)
        self.assertTrue(product.is_active)

    def test_category_creation(self):
        category = Category.objects.create(name='Electronics')
        self.assertEqual(category.name, 'Electronics')
        self.assertIsNotNone(category.created_at)

    def test_supplier_creation(self):
        supplier = Supplier.objects.create(name='ABC Corp')
        self.assertEqual(supplier.name, 'ABC Corp')
        self.assertIsNotNone(supplier.created_at)
