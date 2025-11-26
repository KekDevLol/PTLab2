from django.core.exceptions import ValidationError
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, HttpResponseBadRequest
from django.urls import reverse_lazy
from django.views.generic.edit import CreateView

from .models import Product, Purchase

# Create your views here.
def index(request):
    products = Product.objects.all()
    context = {'products': products}
    return render(request, 'shop/index.html', context)


class PurchaseCreate(CreateView):
    model = Purchase
    fields = ['person', 'address']
    template_name = 'shop/purchase_form.html'

    success_url = reverse_lazy('index')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['product'] = get_object_or_404(Product, pk=self.kwargs['product_id'])
        return context

    def form_valid(self, form):
        product = get_object_or_404(Product, pk=self.kwargs['product_id'])

        if product.quantity <= 0:
            return HttpResponseBadRequest("Товара нет в наличии")

        form.instance.product = product

        try:
            return super().form_valid(form)
        except ValidationError:
            return HttpResponseBadRequest("Товара недостаточно на складе (возможно, только что раскупили)")

