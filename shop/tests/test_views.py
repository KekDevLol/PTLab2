# tests/test_views.py
from django.test import TestCase, Client
from django.urls import reverse

from shop.models import Product, Purchase


class PurchaseCreateTestCase(TestCase):
    def setUp(self):
        self.client = Client()

    def test_webpage_accessibility(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)


class IndexViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        Product.objects.create(name="Телефон", price=30000, quantity=7)
        Product.objects.create(name="Наушники", price=5000, quantity=0)

    def test_index_status_code(self):
        response = self.client.get(reverse('index'))
        self.assertEqual(response.status_code, 200)

    def test_index_shows_quantity_and_disables_buy_when_zero(self):
        response = self.client.get(reverse('index'))
        self.assertContains(response, "7 шт.")
        self.assertContains(response, "Нет в наличии")

        content = response.content.decode()
        buy_links_count = content.count('href="/buy/')
        self.assertEqual(buy_links_count, 1)


class PurchaseCreateViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.p1 = Product.objects.create(name="Планшет", price=25000, quantity=2)
        self.p2 = Product.objects.create(name="Чехол", price=1500, quantity=0)

    def test_buy_page_loads_when_in_stock(self):
        response = self.client.get(reverse('buy', args=[self.p1.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Планшет")

    def test_form_shows_product_name_and_price(self):
        response = self.client.get(reverse('buy', args=[self.p1.id]))
        self.assertContains(response, "Планшет")
        self.assertContains(response, "25000")

    def test_successful_purchase(self):
        response = self.client.post(reverse('buy', args=[self.p1.id]), {
            'person': 'Сергей',
            'address': 'Москва, ул. Тверская'
        }, follow=True)  #  после редиректа получить финальную страницу

        # После редиректа статус 200, а не 302
        self.assertEqual(response.status_code, 200)
        self.assertRedirects(response, reverse('index'))

        self.p1.refresh_from_db()
        self.assertEqual(self.p1.quantity, 1)

        purchase = Purchase.objects.latest('date')
        self.assertEqual(purchase.person, 'Сергей')
        self.assertEqual(purchase.product, self.p1)

    def test_cannot_buy_when_quantity_zero_before_request(self):
        response = self.client.post(reverse('buy', args=[self.p2.id]), {
            'person': 'Кто-то',
            'address': 'Где-то'
        })
        self.assertEqual(response.status_code, 400)
        self.assertIn("нет в наличии", response.content.decode().lower())

    def test_cannot_buy_when_race_condition(self):
        # имитируем одновременные покупки
        for name in ["Первый", "Второй"]:
            Purchase.objects.create(product=self.p1, person=name, address="—")

        self.p1.refresh_from_db()
        self.assertEqual(self.p1.quantity, 0)

        response = self.client.post(reverse('buy', args=[self.p1.id]), {
            'person': 'Опоздал',
            'address': 'Далеко'
        })
        self.assertEqual(response.status_code, 400)
        self.assertIn("товара нет в наличии", response.content.decode().lower())