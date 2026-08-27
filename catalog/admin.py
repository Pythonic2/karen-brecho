from django.contrib import admin

from .models import Category, Product


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'icon', 'image')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'category', 'supplier', 'received_at', 'listed_price', 'sold')
    list_filter = ('sold', 'category', 'supplier', 'received_at')
    search_fields = ('code', 'name', 'description', 'supplier__name', 'supplier__cpf')
    autocomplete_fields = ('supplier',)
    date_hierarchy = 'received_at'
    list_select_related = ('category', 'supplier')

    fieldsets = (
        ('Piece', {'fields': ('code', 'name', 'description', 'image', 'category', 'supplier', 'received_at')}),
        ('Pricing', {'fields': ('listed_price',)}),
        ('Sale status', {'fields': ('sold', 'sold_price')}),
    )
