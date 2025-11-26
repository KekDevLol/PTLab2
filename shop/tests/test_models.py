# tests/test_models.py
from django.test import TestCase
from django.core.exceptions import ValidationError
from datetime import datetime

from shop.models import Product, Purchase


class ProductTestCase(TestCase):
    def setUp(self):
        Product.objects.create(name="book", price=740, quantity=100)
        Product.objects.create(name="pencil", price=50, quantity=50)

    def test_correctness_types(self):
        self.assertIsInstance(Product.objects.get(name="book").name, str)
        self.assertIsInstance(Product.objects.get(name="book").price, int)
        self.assertIsInstance(Product.objects.get(name="pencil").name, str)
        self.assertIsInstance(Product.objects.get(name="pencil").price, int)

    def test_correctness_data(self):
        self.assertEqual(Product.objects.get(name="book").price, 740)
        self.assertEqual(Product.objects.get(name="pencil").price, 50)


class PurchaseTestCase(TestCase):
    def setUp(self):
        self.product_book = Product.objects.create(name="book", price=740, quantity=10)
        self.datetime = datetime.now()

        # колво = 10 > 0
        Purchase.objects.create(
            product=self.product_book,
            person="Ivanov",
            address="Svetlaya St."
        )

    def test_correctness_types(self):
        purchase = Purchase.objects.get(product=self.product_book)
        self.assertIsInstance(purchase.person, str)
        self.assertIsInstance(purchase.address, str)
        self.assertIsInstance(purchase.date, datetime)

    def test_correctness_data(self):
        purchase = Purchase.objects.get(product=self.product_book)
        self.assertEqual(purchase.person, "Ivanov")
        self.assertEqual(purchase.address, "Svetlaya St.")
        self.assertAlmostEqual(
            purchase.date.replace(microsecond=0),
            self.datetime.replace(microsecond=0),
            delta=2  # ±2 секунды для погрешности
        )


class ProductStockTestCase(TestCase):
    def setUp(self):
        self.book = Product.objects.create(name="Python Book", price=1500, quantity=5)
        self.sold_out = Product.objects.create(name="Old Phone", price=10000, quantity=0)

    def test_quantity_default_and_type(self):
        new_product = Product.objects.create(name="Test", price=999)
        self.assertEqual(new_product.quantity, 0)  # default=0
        self.assertIsInstance(new_product.quantity, int)

    def test_can_buy_and_buy_method(self):
        self.assertTrue(self.book.can_buy(3))
        self.assertFalse(self.book.can_buy(10))
        self.assertFalse(self.sold_out.can_buy())

        self.book.buy(2)
        self.book.refresh_from_db()
        self.assertEqual(self.book.quantity, 3)

        with self.assertRaises(ValidationError):
            self.book.buy(10)

        with self.assertRaises(ValidationError):
            self.sold_out.buy()


class PurchaseStockTestCase(TestCase):
    def setUp(self):
        self.product = Product.objects.create(name="Laptop", price=80000, quantity=2)

    def test_purchase_decreases_stock(self):
        initial = self.product.quantity
        Purchase.objects.create(product=self.product, person="Alex", address="Moscow")
        self.product.refresh_from_db()
        self.assertEqual(self.product.quantity, initial - 1)

    def test_cannot_buy_when_no_stock(self):
        # всё купим
        for _ in range(2):
            Purchase.objects.create(product=self.product, person="Bot", address="—")

        self.product.refresh_from_db()
        self.assertEqual(self.product.quantity, 0)

        with self.assertRaises(ValidationError):
            Purchase.objects.create(product=self.product, person="Late", address="Far")