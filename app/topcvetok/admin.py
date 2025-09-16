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


@admin.register(models.Blog)
class BlogAdmin(admin.ModelAdmin):
    list_display = [field.name for field in models.Blog._meta.fields]
    search_fields = [field.name for field in models.Blog._meta.fields]


@admin.register(models.Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = [field.name for field in models.Project._meta.fields]
    search_fields = [field.name for field in models.Project._meta.fields]


@admin.register(models.Mail)
class MailAdmin(admin.ModelAdmin):
    list_display = [field.name for field in models.Mail._meta.fields]
    search_fields = [field.name for field in models.Mail._meta.fields]
