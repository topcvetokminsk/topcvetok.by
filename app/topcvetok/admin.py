from django.contrib import admin

from topcvetok import models


@admin.register(models.Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = [field.name for field in models.Account._meta.fields]
    search_fields = [field.name for field in models.Account._meta.fields]

    def save_model(self, request, obj, form, change):
        if "argon2" not in obj.password:
            obj.set_password(obj.password)
        obj.save()


@admin.register(models.Banner)
class BannerAdmin(admin.ModelAdmin):
    list_display = [field.name for field in models.Banner._meta.fields]
    search_fields = [field.name for field in models.Banner._meta.fields]
    readonly_fields = ['id']


@admin.register(models.Video)
class VideoAdmin(admin.ModelAdmin):
    list_display = [field.name for field in models.Video._meta.fields]
    search_fields = [field.name for field in models.Video._meta.fields]
    readonly_fields = ['id']


@admin.register(models.Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = [field.name for field in models.Category._meta.fields]
    search_fields = [field.name for field in models.Category._meta.fields]
    list_filter = ['is_active']
    readonly_fields = ['id']

    def level_display(self, obj):
        return obj.level
    level_display.short_description = "Уровень"


@admin.register(models.Attribute)
class AttributeAdmin(admin.ModelAdmin):
    list_display = [field.name for field in models.Attribute._meta.fields]
    search_fields = [field.name for field in models.Attribute._meta.fields]
    list_filter = ['is_active']
    readonly_fields = ['id']


@admin.register(models.Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = [field.name for field in models.Product._meta.fields]
    search_fields = [field.name for field in models.Product._meta.fields]
    list_filter = ['is_available', 'categories', 'created_at']
    readonly_fields = ['id', 'created_at', 'updated_at']
    filter_horizontal = ['categories']

    # Вариации товара инлайном
    class ProductVariantInline(admin.TabularInline):
        model = models.ProductVariant
        extra = 0
        fields = ['price', 'promotional_price', 'is_available']

    inlines = [ProductVariantInline]

    def categories_display(self, obj):
        return ", ".join([cat.name for cat in obj.categories.all()[:3]])
    categories_display.short_description = "Категории"


@admin.register(models.Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = [field.name for field in models.Service._meta.fields]
    search_fields = [field.name for field in models.Service._meta.fields]
    list_filter = ['is_available', 'created_at']
    readonly_fields = ['id', 'created_at', 'updated_at']

    def price_display(self, obj):
        return obj.get_price_display()
    price_display.short_description = "Цена"

    def is_free_display(self, obj):
        return "Да" if obj.is_free else "Нет"
    is_free_display.short_description = "Бесплатная"


# Админ для вариаций и их атрибутов
class ProductVariantAttributeInline(admin.TabularInline):
    model = models.ProductVariantAttribute
    extra = 0
    autocomplete_fields = ['attribute']


@admin.register(models.ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = ['id', 'product', 'price', 'promotional_price', 'is_available', 'created_at']
    search_fields = ['id', 'product__name']
    list_filter = ['is_available', 'created_at', 'product']
    readonly_fields = ['id', 'created_at', 'updated_at']
    inlines = [ProductVariantAttributeInline]


@admin.register(models.ProductVariantAttribute)
class ProductVariantAttributeAdmin(admin.ModelAdmin):
    list_display = ['id', 'variant', 'attribute']
    search_fields = ['id', 'variant__product__name', 'attribute__name', 'attribute__value']
    readonly_fields = ['id']


@admin.register(models.Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = [field.name for field in models.Order._meta.fields]
    search_fields = [field.name for field in models.Order._meta.fields]
    list_filter = ['payment_method', 'delivery_method', 'created_at']
    readonly_fields = ['id', 'created_at', 'updated_at']


@admin.register(models.Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = [field.name for field in models.Review._meta.fields]
    search_fields = [field.name for field in models.Review._meta.fields]
    readonly_fields = ['id']


@admin.register(models.Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = [field.name for field in models.Contact._meta.fields]
    search_fields = [field.name for field in models.Contact._meta.fields]
    readonly_fields = ['id']
