#!/usr/bin/env python
# -- coding: utf-8 --
"""

"""
from django.urls import path
from urlopen_app.views import  LoginAPIView, ControlerViewSet


app_name = 'urlopen_app'

urlpatterns = [
    #---------------api-----------------------------
    # path('users/login/', LoginAPIView.as_view()),

    #извлечение и сохранение html из url
    path('loader/nexturl/<int:cnt>/', ControlerViewSet.as_view({"get":"get_next_urls"})),  #возвращает следующие cnt url-ок для loadera
    path('puthtml/<int:pk>/', ControlerViewSet.as_view({"put":"put_html"})),    #принимает url-ки от loadera и изменяет запись по pk добавляя новый статус и html текст

    #извлечение и сохранение url из html
    path('parser/give-html/<int:cnt>/', ControlerViewSet.as_view({"get":"get_next_html"})),    #отправляет следующие cnt html-ек для парсера
    path('parser/posturl/<int:site_pk>/<int:page_pk>/', ControlerViewSet.as_view({"post":"post_url"})),    #для получения списка url-ok

    #определение типа страницы
    path('parser/get-category-url/<int:cnt>/', ControlerViewSet.as_view({"get":"get_url_category"})),    #отправляет n количество url для определения категории страницы
    path('parser/postcategory/', ControlerViewSet.as_view({"post":"post_category"})),    #получаем словарь с id и новыми статусами категорий

    #ивлечение товара
    path('factory/give-html/<int:cnt>/', ControlerViewSet.as_view({"get":"get_next_html_factory"})),    #для отправки html для получения основной информации о товаре
    path('factory/post-item/<int:site_pk>/<int:page_pk>/', ControlerViewSet.as_view({"post":"post_item"})),    #получаем товар с информацией

    #извлечение url картиное
    path('parser/get-picture-url/<int:cnt>/', ControlerViewSet.as_view({"get":"get_extract_image"})),    #отправление в loader для извлечения картинок
    path('parser/post-picture-url/<int:site_pk>/<int:page_pk>/', ControlerViewSet.as_view({"post":"post_picture_url"})),    #добавление url картинок

    #для извлечения base64 картинки
    path('loader/next-image-url/<int:cnt>/', ControlerViewSet.as_view({"get":"extract_base64"})),    #отправка url картинок на извлечение base64
    path('putbase64/<int:site_pk>/<int:page_pk>/', ControlerViewSet.as_view({'put':'put_base64'})),    #добавление base64 картинки

    #декодирование картинок
    # path('decode/image_url/<int:cnt>/', ControlerViewSet.as_view({"get":"decode_image"})),    #отправление в parser для декодирования картинки
    # path('decode/post_image_url/<int:page_pk>/', ControlerViewSet.as_view({"post":"post_image"})),    #получение нового статуса картинки

    #для добавления attempta
    path('change-status/<int:page_pk>/', ControlerViewSet.as_view({"put":"attempt_error"})),    #специальный метод для страниц, с которыми происходили какие либо ошибки, метод работает с attempt и принимает статус страницы

]