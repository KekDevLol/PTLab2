from django.core.exceptions import ValidationError
from django.db import models, transaction

# Create your models here.
class Product(models.Model):
    name = models.CharField(max_length=200)
    price = models.PositiveIntegerField()
    quantity = models.PositiveIntegerField(default=0)

    def can_buy(self, count=1):
        return self.quantity >= count

    def buy(self, count=1):
        if not self.can_buy(count):
            raise ValidationError(f"Недостаточно товара {self.name} на складе")
        self.quantity -= count
        self.save(update_fields=['quantity'])

    def clean(self):
        if self.quantity < 0:
            raise ValidationError("количество не может быть отрицательным")


class Purchase(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    person = models.CharField(max_length=200)
    address = models.CharField(max_length=200)
    date = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if self.pk is None:  # только при создании новой покупки
            # Что бы откатиться если ошибки
            with transaction.atomic():
                product = Product.objects.select_for_update().get(pk=self.product_id)
                product.buy()  # уменьшаем на 1 штуку
        super().save(*args, **kwargs)
