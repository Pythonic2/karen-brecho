from django.shortcuts import render

from .models import Category, Product


def home(request):
    return render(request, 'catalog/welcome.html')


def shop(request):
    products = Product.objects.filter(sold=False).select_related('category', 'supplier')
    categories = Category.objects.all()
    query = request.GET.get('q', '').strip()
    category_slug = request.GET.get('category', '').strip()

    if query:
        products = products.filter(name__icontains=query)
    if category_slug:
        products = products.filter(category__slug=category_slug)

    template = 'catalog/partials/product_grid.html' if request.headers.get('HX-Request') else 'catalog/shop.html'
    return render(request, template, {
        'products': products,
        'categories': categories,
        'query': query,
        'selected_category': category_slug,
    })
