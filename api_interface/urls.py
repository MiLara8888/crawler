#!/usr/bin/env python
# -- coding: utf-8 --
"""

"""
from django.urls import path


from api_interface.views import ApiInterfaceViewSet, ApiInterfaceTokenViewSet
from django.urls import path



urlpatterns = [
    #---------------api-----------------------------
    path('<str:typeof>/login/', ApiInterfaceTokenViewSet.as_view({"post":"autorization_get_token"}), name='login'),    #получение токена по username и password

    # path('<str:typeof>/refresh/', ApiInterfaceViewSet.as_view({"post":"refresh_token"}), name='refresh'),    #получение токена по username и password

    path("<str:typeof>/site/<int:against>/<int:count>", ApiInterfaceViewSet.as_view({"post":"sites_info"})),    #отдача данных о сайтах в json и xml

    path("<str:typeof>/site/<str:domain_name>", ApiInterfaceViewSet.as_view({"post":"site_info"})),    #отдача данных о сайте в json и xml

    path("<str:typeof>/site/<str:domain_name>/item/<int:against>/<int:count>", ApiInterfaceViewSet.as_view({"post":"items_info"})),    #отдача данных о товарах в json и xml

    path("<str:typeof>/site/<str:domain_name>/item/<int:id>", ApiInterfaceViewSet.as_view({"post":"item_info"})),    #отдача данных о товаре в json и xml по id товара

    # path("user/get_jwt_token", ApiInterfaceViewSet.as_view({"post":"create_jwt"})),     #получение токена для пользователя, который есть в базе users


]