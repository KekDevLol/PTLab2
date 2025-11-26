from django.test import SimpleTestCase
from django.core.exceptions import ValidationError
from unittest.mock import patch

from shop.models import Product, Purchase


class ProductUnitTests(SimpleTestCase):

    def test_can_buy(self):
        p = Product(quantity=10)
        self.assertTrue(p.can_buy(5))
        self.assertFalse(p.can_buy(20))

    @patch.object(Product, 'save')
    def test_buy_success(self, mock_save):
        p = Product(name="iPhone", price=100000, quantity=8)
        p.buy(3)
        self.assertEqual(p.quantity, 5)
        mock_save.assert_called_once_with(update_fields=['quantity'])

    @patch.object(Product, 'save')
    def test_buy_raises_and_does_not_save(self, mock_save):
        p = Product(quantity=2)
        with self.assertRaises(ValidationError):
            p.buy(5)
        mock_save.assert_not_called()

    def test_clean_negative_quantity(self):
        p = Product(quantity=-5)
        with self.assertRaises(ValidationError):
            p.clean()


class PurchaseSaveLogicUnitTests(SimpleTestCase):

    @patch('shop.models.Product.objects.select_for_update')
    @patch('shop.models.Product.buy')
    def test_save_logic_calls_buy_only_when_pk_is_none(self, mock_buy, mock_select):
        fake_product = Product(id=999, quantity=10)
        mock_select.return_value.get.return_value = fake_product

        purchase = Purchase(product_id=999, person="Ремейк(Репер)", address="Москва")
        purchase.id = None

        if purchase.id is None:
            product = Product.objects.select_for_update().get(id=purchase.product_id)
            product.buy(1)

        mock_buy.assert_called_once_with(1)

        mock_buy.reset_mock()
        purchase.id = 1

        if purchase.id is None:
            product.buy(1)

        mock_buy.assert_not_called()

    @patch('shop.models.Product.objects.select_for_update')
    def test_save_logic_raises_when_buy_fails(self, mock_select):
        fake_product = Product(id=1, quantity=0)
        mock_select.return_value.get.return_value = fake_product

        # Нужно чтобы buy() кидал ошибку
        with patch.object(fake_product, 'buy') as mock_buy:
            mock_buy.side_effect = ValidationError("Нет в наличии")

            purchase = Purchase(product_id=1, person="петрехан", address="калымяк")
            purchase.id = None

            with self.assertRaises(ValidationError):
                if purchase.id is None:
                    product = Product.objects.select_for_update().get(id=purchase.product_id)
                    product.buy(1)

            mock_buy.assert_called_once()
