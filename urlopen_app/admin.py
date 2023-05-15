#!/usr/bin/env python
# -- coding: utf-8 --
"""
админка
"""
from django.contrib import admin
from urlopen_app.models import User, Site, Page, Item


@admin.action(description='Html станицы не извлекался')
def set_state_20(modeladmin, request, queryset):
    queryset.update(status=20)

@admin.action(description='HTML успешно извлечён страница готова к извлечению url-ок')
def set_state_30(modeladmin, request, queryset):
    queryset.update(status=30)

@admin.action(description='Из страницы успешно извлечены url страница готова к определению типа')
def set_state_32(modeladmin, request, queryset):
    queryset.update(status=32)

@admin.action(description='Тип страницы успешно определён, страница готова к отправке на фабрику')
def set_state_52(modeladmin, request, queryset):
    queryset.update(status=52)

@admin.action(description='Страница обработана, товар извлечён, готова к извлечению url-ok картинок товара')
def set_state_0(modeladmin, request, queryset):
    queryset.update(status=0)

@admin.action(description='Страница не содержит url')
def set_state_93(modeladmin, request, queryset):
    queryset.update(status=93)

@admin.action(description='Картинка не извлекалась')
def set_state_3(modeladmin, request, queryset):
    queryset.update(status=3)


@admin.action(description='Картинка готова к декодированию')
def set_state_5(modeladmin, request, queryset):
    queryset.update(status=5)


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'is_staff')
    search_fields = ('username', )
    list_filter = ('is_staff' ,)


@admin.register(Site)
class SiteAdmin(admin.ModelAdmin):
    list_display = ('domain_name', 'time_create', 'time_update')        #отображение в списке
    list_display_links = ('domain_name', )         #поля будут ссылками
    search_fields = ('domain_name', )          #поля поиска
    readonly_fields = ('time_create', 'time_update')
    save_on_top = True


@admin.register(Page)
class PageAdmin(admin.ModelAdmin):
    raw_id_fields = ['site', ]
    list_select_related = ['site', ]
    list_display = ('id', 'type_page', 'status', 'time_create', 'time_update', 'image_item_id')
    # list_display = ('url',)
    # search_fields = ('url','id',)
    search_fields = ('url', 'id', 'image_page__id')
    # search_fields = ('image_counter',)
    # search_fields = ('attempts', )
    list_filter = ('type_page', 'status', 'site__domain_name')       #фильтрация
    fields = ('site', 'url', 'status', 'type_page', 'json_data', 'attempts', 'status_description', 'image_counter', 'time_create', 'time_update', 'html_page', 'image_path')    #указывать явно если нужна определенная последовательность или явно нужны ОПРЕДЕЛЕННЫЕ ПОЛЯ
    # ordering=('-time_update',)    #закоментить, чтобы база работала быстрее
    readonly_fields = ('time_update', 'time_create')
    save_on_top = True
    actions = [set_state_20, set_state_30, set_state_32, set_state_52, set_state_0, set_state_93, set_state_3, set_state_5]


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    fields = ('name', 'unit', 'wholesale_price', 'sales_price', 'vendor_code', 'site_code', 'brand', 'json_data', 'time_create', 'time_update', )
    list_display = ('name', 'vendor_code', 'sales_price', 'brand', 'time_create', 'time_update')
    # search_fields = ('id', 'name', 'vendor_code', 'site_code')
    search_fields = ('vendor_code',)
    # list_filter = ('site__domain_name',)       #фильтрация
    # ordering=('-time_update',)
    readonly_fields = ('time_update', 'time_create')
    save_on_top = True


admin.site.site_header = ('Админ-панель веб краулера')
admin.site.site_title = ('Админ-панель веб краулера')
admin.site.empty_value_display = '(None)'