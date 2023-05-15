#!/usr/bin/env python
# -- coding: utf-8 --
"""

"""
from django.db import models
from urlopen_app.edt import ChoicesStatus, ChoicesPage
import jwt
from datetime import datetime, timedelta
from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from urlopen_app.edt import ChoicesStatus



import jwt
from datetime import datetime, timedelta
from django.conf import settings
from django.contrib.auth.models import (AbstractBaseUser, BaseUserManager, PermissionsMixin)
from django.db import models



class UserManager(BaseUserManager):
    """
    Django требует, чтобы кастомные пользователи определяли свой собственный
    класс Manager. Унаследовавшись от BaseUserManager, мы получаем много того
    же самого кода, который Django использовал для создания User (для демонстрации).
    """

    def create_user(self, username, password=None):
        """ Создает и возвращает пользователя с паролем и именем. """
        if username is None:
            raise TypeError('Пользователю нужно имя')

        user = self.model(username=username)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, username, password):
        """ Создает и возввращет пользователя с привилегиями суперадмина. """
        if password is None:
            raise TypeError('Суперпользователь должен иметь пароль')
        if username is None:
            raise TypeError('Пользователю нужно имя')

        user = self.create_user(username, password)
        user.is_superuser = True
        user.is_staff = True
        user.save()
        return user


class User(AbstractBaseUser, PermissionsMixin):
    username = models.CharField(db_index=True, max_length=255, unique=True, verbose_name='Идентификатор пользователя')
    # email = models.EmailField(db_index=True, unique=True)
    # is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False, verbose_name='Флаг администраторов')
    # Свойство USERNAME_FIELD сообщает нам, какое поле мы будем использовать для входа в систему.
    USERNAME_FIELD = 'username'
    # REQUIRED_FIELDS = ['username']

    # Сообщает Django, что определенный выше класс UserManager
    # должен управлять объектами этого типа.
    objects = UserManager()

    def __str__(self):
        return self.username

    @property
    def token(self):
        """
        Позволяет получить токен пользователя путем вызова user.token, вместо
        user._generate_jwt_token(). Декоратор @property выше делает это
        возможным. token называется "динамическим свойством".
        """
        return self._generate_jwt_token()

    def get_full_name(self):
        """
        Этот метод требуется Django для таких вещей, как обработка электронной
        почты. Обычно это имя фамилия пользователя, но поскольку мы не
        используем их, будем возвращать username.
        """
        return self.username

    def get_short_name(self):
        """ Аналогично методу get_full_name(). """
        return self.username

    def _generate_jwt_token(self):
        """
        Генерирует веб-токен JSON, в котором хранится идентификатор этого
        пользователя, срок действия токена составляет 1 день от создания
        """
        dt = datetime.now() + timedelta(days=2)
        token = jwt.encode({
            'id': self.pk,
            'exp': int(dt.strftime('%s'))
        }, settings.SECRET_KEY, algorithm='HS256')
        return token

    def save(self, *args, **kwargs) -> None:
        self.set_password(self.password)
        return super().save(*args, **kwargs)

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'



class Site(models.Model):
    '''
    хранение ссылок и доменных имён сайтов для скрапинга основная модель
    '''
    domain_name = models.CharField(max_length=255, unique=True, verbose_name='Доменное имя')
    url = models.CharField(max_length=1000, blank=True, verbose_name='URL сайта')
    time_create = models.DateTimeField(auto_now_add=True, verbose_name='Время создания')
    time_update = models.DateTimeField(auto_now=True, verbose_name='Время изменения')
    json_data = models.JSONField(blank=True, null=True, verbose_name='Метаданные')
    # колличество попыток для обработки страницы
    attempts = models.PositiveSmallIntegerField(default=5, verbose_name='Колличество попыток для обработки страницы для этого сайта')
    pattern_path = models.CharField(max_length=1000, blank=True, null=True, verbose_name='Паттерн пути для сохранения картинок')

    def __str__(self):
        return self.domain_name

    class Meta:
        verbose_name = 'Сайт'
        verbose_name_plural = 'Сайты'


class CommonAbstractModel(models.Model):
    """
        Абстрактная модель для хранения общих данных
        Абстрактная модель не создает таблицу в базе данных при запуске миграций, но зато от неё можно наследоваться и расширять наши модели.
    """
    site = models.ForeignKey(Site, on_delete=models.PROTECT, default=None, verbose_name='Сайт')  # сайт будет у всех моделей
    time_create = models.DateTimeField(auto_now_add=True, verbose_name='Время создания')
    time_update = models.DateTimeField(auto_now=True, verbose_name='Время изменения')
    json_data = models.JSONField(null=True, blank=True, verbose_name='json')
    attempts = models.PositiveSmallIntegerField(default=0, verbose_name='Колличество попыток использованых для обработки')

    class Meta:
        abstract = True




class Page(CommonAbstractModel):
    '''
    хранение url с страниц сайта , html и статуса
    '''
    # ещё site, time_create, time_update, json_data

    html_page = models.TextField(blank=True, null=True, verbose_name='html страницы или base64 картинки')  # Поле для хранения html
    status = models.IntegerField(choices=ChoicesStatus.choices, db_index=True, verbose_name='Статус исполнения', default=ChoicesStatus.NOT_PROCESSED_HTML)
    type_page = models.IntegerField(choices=ChoicesPage.choices, db_index=True, verbose_name='Тип страницы', default=ChoicesPage.NONE)
    status_description = models.CharField(max_length=300, verbose_name='Описание статуса', default='Html станицы не извлекался')
    url = models.CharField(max_length=1000, verbose_name='URL страницы')
    image_item = models.ForeignKey("Item", on_delete=models.CASCADE, null=True, blank=True, verbose_name='Товар связанная модель', related_name='related_image_item')
    image_page = models.ForeignKey("Page", on_delete=models.CASCADE, null=True, blank=True, verbose_name='Страница связанная модель',  related_name='related_image_page')
    image_counter = models.IntegerField(default=0, verbose_name='уникальный числовой идентификатор картинки')
    image_type = models.CharField(max_length=7, null=True, blank=True, verbose_name = 'разрешение картинки')
    image_path = models.CharField(max_length=1000, blank=True, null=True, verbose_name='path картинки')  # Поле для хранения html


    def update(self, *args, **kwargs):
        self.status_description = str(ChoicesStatus(self.status).label)
        super().update(*args, **kwargs)
    def save(self, *args, **kwargs):
        self.status_description = str(ChoicesStatus(self.status).label)
        super().save(*args, **kwargs)


    def get_type_page(self):
        return ChoicesPage(self.type_page).label

    def get_status(self):
        return ChoicesStatus(self.status).label

    class Meta:
        verbose_name = 'Страница сайта'
        verbose_name_plural = 'Страницы сайтов'
        unique_together = ['site', 'url']  # уникальность полей в связке
        ordering = ['-time_update']
        app_label = 'urlopen_app'
        indexes = [
            models.Index(fields=['time_update', 'status'], name='update_time'),
        ]


    def __str__(self):
        return self.url


class Item(CommonAbstractModel):
    '''
    хранение информации о товаре
    '''
    # page, name, unit, wholesale_price, sales_price, site_code, vendor_code, brand, site, time_create, time_update, json_data
    page = models.ForeignKey(Page, on_delete=models.CASCADE, verbose_name='Страница связанная модель',default=None)
    name = models.CharField(max_length=300, verbose_name='Имя товара')
    unit = models.CharField(max_length=30, blank=True, null=True, verbose_name='Единица измерения')
    wholesale_price = models.DecimalField(decimal_places=4, default=0, max_digits=13, null=True, blank=True, verbose_name='Оптовая стоимость товара')
    sales_price = models.DecimalField(decimal_places=4, max_digits=13, default=0, null=True, blank=True, verbose_name='Розничная стоимость товара')
    vendor_code = models.CharField(max_length=100, blank=True, null=True, verbose_name='Артикул')
    site_code = models.CharField(max_length=100, blank=True, null=True, verbose_name='Уникальный идентификатор на сайте')
    brand = models.CharField(max_length=200, blank=True, db_index=True, null=True, verbose_name='Бренд')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Товар'
        verbose_name_plural = 'Товары'
        # уникальность полей в связке
        unique_together = ['site','vendor_code','name']
        ordering = ['-time_update']
