#!/usr/bin/env python
# -- coding: utf-8 --
"""
сериализация объектов
"""
from rest_framework import serializers
from django.contrib.auth import authenticate
from urlopen_app.models import Site, Page, Item


class ImageDecodeSerializer(serializers.ModelSerializer):

    """ для возвращения в loader и parser информации для переработки """

    domain_name = serializers.SerializerMethodField(read_only=True)
    brand = serializers.SerializerMethodField(read_only=True)
    vendor_code = serializers.SerializerMethodField(read_only=True)
    pattern_path = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Page
        fields = ('id', 'html_page', 'image_type', 'image_counter', 'time_create', 'time_update', 'domain_name', 'site_id',  'brand', 'vendor_code', 'image_item_id', 'pattern_path')

    def get_domain_name(self, obj):
        return obj.site.domain_name

    def get_brand(self, obj):
        return obj.image_item.brand

    def get_vendor_code(self, obj):
        return obj.image_item.vendor_code

    def get_pattern_path(self, obj):
        return obj.site.pattern_path


class DictTypeSerializer(serializers.ModelSerializer):
    """для получения словаря с id и типом страницы"""
    #parser/postcategory/    :post
    result_list = serializers.ListField()

    class Meta:
        model = Page
        fields = ('result_list',)


class ParserPostSerializer(serializers.ModelSerializer):
    """Для получения списка url-ok со страницы"""
    #parser/posturl/    :post
    url_list = serializers.ListField()

    # status = serializers.IntegerField()
    # site = serializers.IntegerField()
    # id = serializers.IntegerField()

    class Meta:
        model = Page
        fields = ('url_list','status','site','id')


class PictureUrlSerializer(serializers.ModelSerializer):
    """ для добавления url картинок """

    picture_list = serializers.ListField(allow_empty=True)

    class Meta:
        model = Page
        fields = ('picture_list',)




class LoaderNextSerializer(serializers.ModelSerializer):

    """ для возвращения в loader и parser информации для переработки """

    #loader/nexturl/<int:cnt>/   :get
    #parser/get-category-url/<int:cnt>/    :get
    #parser/give-html/<int:cnt>    :get

    domain_name = serializers.SerializerMethodField(read_only=True)
    attempt_site = serializers.SerializerMethodField(read_only=True)
    meta_url = serializers.SerializerMethodField(read_only=True)
    site_id = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Page
        fields = ('html_page', 'url', 'site', 'id', 'status',
                  'attempt_site', 'domain_name', 'meta_url', 'site_id')

    def get_domain_name(self, obj):
        return obj.site.domain_name

    def get_attempt_site(self, obj):
        return obj.site.attempts

    def get_meta_url(self, obj):
        return obj.site.json_data

    def get_site_id(self,obj):
        return obj.site.id


class GetHtmlSerialiser(serializers.ModelSerializer):
    """для получения html"""
    #puthtml/<int:pk>/    :put

    # html_page = serializers.CharField(allow_blank=True)
    # status = serializers.IntegerField()

    class Meta:
        model = Page
        fields = ('html_page','status')


class PostItemSerializer(serializers.ModelSerializer):
    """Для проучения в post запросе информации о товаре"""
    #factory/post-item/
    # name = serializers.CharField(max_length=300)
    # unit = serializers.CharField(max_length=30, allow_blank=True, allow_null=True)
    # wholesale_price = serializers.DecimalField(decimal_places = 4,default=0, allow_null=True,  max_digits = 13)
    # sales_price = serializers.DecimalField(decimal_places = 4, default=0, allow_null=True, max_digits = 13)
    # vendor_code = serializers.CharField(max_length=100, allow_blank=True, allow_null=True)
    # site_code = serializers.CharField(max_length=100, allow_blank=True, allow_null=True)
    # json_data = serializers.DictField(allow_empty=True)
    # brand = serializers.CharField(max_length=200, allow_blank=True, allow_null=True)

    class Meta:
        model = Item
        fields = ('name', 'unit', 'wholesale_price', 'sales_price', 'vendor_code', 'site_code', 'json_data', 'brand')



class AttemptSerializer(serializers.ModelSerializer):
    """Для получения в put запросе нового статуса"""
    status = serializers.IntegerField()

    class Meta:
        model = Page
        fields = ('status',)



class DecodeSerializer(serializers.ModelSerializer):
    """получение информации о извлечённой в папку картинки"""
    class Meta:
        model = Page
        fields = ('status', 'image_path')




class LoginSerializer(serializers.Serializer):
    """класс авторизации"""

    username = serializers.CharField(max_length=255)
    password = serializers.CharField(max_length=128, write_only=True)
    token = serializers.CharField(max_length=255, read_only=True)

    def create(self, validated_data):
        return super().create(validated_data)

    def update(self, instance, validated_data):
        return super().update(instance, validated_data)

    def validate(self, attrs):
        # В методе validate мы убеждаемся, что текущий экземпляр
        # LoginSerializer значение valid. В случае входа пользователя в систему
        # это означает подтверждение того, что присутствуют адрес электронной
        # почты и то, что эта комбинация соответствует одному из пользователей.
        user_name = attrs.get('username', None)
        password = attrs.get('password', None)

        # Вызвать исключение, если не предоставлена почта.
        if user_name is None:
            raise serializers.ValidationError(
                'Нужен юзернейм'
            )

        # Вызвать исключение, если не предоставлен пароль.
        if password is None:
            raise serializers.ValidationError(
                'Нужен пароль'
            )

        # Метод authenticate предоставляется Django и выполняет проверку, что
        # предоставленные почта и пароль соответствуют какому-то пользователю в
        # нашей базе данных. Мы передаем email как username, так как в модели
        # пользователя USERNAME_FIELD = email.
        user = authenticate(username=user_name, password=password)

        # Если пользователь с данными почтой/паролем не найден, то authenticate
        # вернет None. Возбудить исключение в таком случае.
        if user is None:
            raise serializers.ValidationError(
                'Нет пользователя с таким логином и паролем'
            )

        # Метод validate должен возвращать словать проверенных данных. Это
        # данные, которые передются в т.ч. в методы create и update.
        return {
            'username': user.username,
            'token': user.token
        }