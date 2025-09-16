from django.contrib import admin
from django.utils.html import format_html

from topcvetok import models


@admin.register(models.Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ['login', 'email', 'first_name', 'last_name', 'phone', 'is_active', 'date_joined']
    search_fields = ['login', 'email', 'first_name', 'last_name', 'phone']
    list_filter = ['is_active', 'is_staff', 'date_joined']
    readonly_fields = ['id', 'date_joined', 'last_login']

    def save_model(self, request, obj, form, change):
        if "argon2" not in obj.password:
            obj.set_password(obj.password)
        obj.save()


@admin.register(models.Banner)
class BannerAdmin(admin.ModelAdmin):
    list_display = ['title', 'link', 'photo_preview']
    search_fields = ['title', 'text']
    readonly_fields = ['id']

    def photo_preview(self, obj):
        if obj.photo:
            return format_html('<img src="{}" width="100" height="60" />', obj.photo.url)
        return "Нет фото"
    photo_preview.short_description = "Превью"


@admin.register(models.Video)
class VideoAdmin(admin.ModelAdmin):
    list_display = ['slug', 'video_preview']
    search_fields = ['slug']
    readonly_fields = ['id']

    def video_preview(self, obj):
        if obj.video:
            return format_html('<video width="100" height="60" controls><source src="{}" type="video/mp4"></video>', obj.video.url)
        return "Нет видео"
    video_preview.short_description = "Превью"


@admin.register(models.Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'parent', 'slug', 'is_active', 'level_display']
    search_fields = ['name', 'slug', 'keyword']
    list_filter = ['is_active', 'parent']
    readonly_fields = ['id', 'level_display']
    prepopulated_fields = {'slug': ('name',)}

    def level_display(self, obj):
        return obj.level
    level_display.short_description = "Уровень"


@admin.register(models.AttributeType)
class AttributeTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'is_active', 'is_filterable', 'display_order']
    search_fields = ['name', 'slug', 'description']
    list_filter = ['is_active', 'is_filterable']
    readonly_fields = ['id']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(models.Attribute)
class AttributeAdmin(admin.ModelAdmin):
    list_display = ['display_name', 'attribute_type', 'price_modifier', 'is_active']
    search_fields = ['display_name', 'attribute_type__name']
    list_filter = ['attribute_type', 'is_active']
    readonly_fields = ['id']


@admin.register(models.Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'price', 'promotional_price', 'is_available', 'photo_preview', 'categories_display']
    search_fields = ['name', 'description', 'slug']
    list_filter = ['is_available', 'categories', 'created_at']
    readonly_fields = ['id', 'created_at', 'updated_at']
    filter_horizontal = ['categories']
    prepopulated_fields = {'slug': ('name',)}

    def photo_preview(self, obj):
        if obj.photo:
            return format_html('<img src="{}" width="100" height="60" />', obj.photo.url)
        return "Нет фото"
    photo_preview.short_description = "Превью"

    def categories_display(self, obj):
        return ", ".join([cat.name for cat in obj.categories.all()[:3]])
    categories_display.short_description = "Категории"


@admin.register(models.Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ['name', 'price_display', 'is_available', 'is_free_display']
    search_fields = ['name', 'description']
    list_filter = ['is_available', 'created_at']
    readonly_fields = ['id', 'created_at', 'updated_at']

    def price_display(self, obj):
        return obj.get_price_display()
    price_display.short_description = "Цена"

    def is_free_display(self, obj):
        return "Да" if obj.is_free else "Нет"
    is_free_display.short_description = "Бесплатная"




@admin.register(models.Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_number', 'customer_name', 'customer_phone', 'total_amount', 'status', 'created_at']
    search_fields = ['order_number', 'customer_name', 'customer_phone', 'delivery_address']
    list_filter = ['status', 'payment_method', 'delivery_method', 'created_at']
    readonly_fields = ['id', 'order_number', 'created_at', 'updated_at', 'consent_date']


@admin.register(models.Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['customer_name', 'rating', 'is_approved', 'created_at']
    search_fields = ['customer_name', 'comment']
    list_filter = ['rating', 'is_approved', 'created_at']
    readonly_fields = ['id', 'created_at']


@admin.register(models.Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ['name', 'phone', 'email', 'created_at']
    search_fields = ['name', 'phone', 'email', 'message']
    list_filter = ['created_at']
    readonly_fields = ['id', 'created_at']
