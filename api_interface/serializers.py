#!/usr/bin/env python
# -- coding: utf-8 --
"""
сериализация объектов
"""
from rest_framework import serializers
from django.contrib.auth import authenticate
from urlopen_app.models import Site, Page, Item
from datetime import datetime, timedelta

from django.contrib.auth import get_user_model
from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
import jwt
from html_urlopen.settings import JWT_ACCESS_TTL, JWT_REFRESH_TTL, JWT_SECRET, SECRET_KEY



class ItemSerializer(serializers.ModelSerializer):
    """Отдача информации о товарах для ApiInterfaceVieм"""
    #'<str:typeof>/site/<str:domain_name>/items/<int:from>/<int:count>
    #<<str:typeof>/site/<str:domain_name>/item/<int:id>

    class Meta:
        model = Item
        fields = '__all__'


class SiteSerializer(serializers.ModelSerializer):
    """информация о сайтах"""
    #'<str:type>/site/<str:domain_name>'
    #'<str:typeof>/site/<int:against>/<int:count>

    class Meta:
        model = Site
        fields = ('id', 'domain_name', 'url', 'time_create')


UserModel = get_user_model()



# # JWT_ACCESS_TTL ЗДЕСЬ ЭТО КОРОТКИЙ(ПО ВРЕМЕНИ) ТОКЕН
# # JWT_REFRESH_TTL ЗДЕСЬ ЭТО ДЛИННЫЙ(ПО ВРЕМЕНИ ЖИЗНИ) ТОКЕН
# class LoginSerializer(serializers.Serializer):
#     # ==== INPUT ====
#     username = serializers.CharField(required=True, write_only=True)
#     password = serializers.CharField(required=True, write_only=True)
#     # ==== OUTPUT ====
#     access = serializers.CharField(read_only=True)
#     refresh = serializers.CharField(read_only=True)


#     def validate(self, attrs):
#         # standard validation
#         validated_data = super().validate(attrs)

#         # validate email and password
#         username = validated_data['username']
#         password = validated_data['password']
#         error_msg = _('username или password не корректны')
#         try:
#             user = UserModel.objects.get(username=username)
#             if not user.check_password(password):
#                 raise serializers.ValidationError(error_msg)
#             validated_data['user'] = user
#         except UserModel.DoesNotExist:
#             raise serializers.ValidationError(error_msg)

#         return validated_data

#     def create(self, validated_data):
#         dt = datetime.now() + timedelta(days=2)
#         token = jwt.encode({
#             'iss': 'api_interface',
#             'id': validated_data['user'].id,
#             'exp': int(dt.strftime('%s'))
#         }, SECRET_KEY, algorithm='HS256')

#         return {
#                 "token":token
#                 }



# JWT_ACCESS_TTL ЗДЕСЬ ЭТО КОРОТКИЙ(ПО ВРЕМЕНИ) ТОКЕН
# JWT_REFRESH_TTL ЗДЕСЬ ЭТО ДЛИННЫЙ(ПО ВРЕМЕНИ ЖИЗНИ) ТОКЕН
class LoginSerializer(serializers.Serializer):
    # ==== INPUT ====
    username = serializers.CharField(required=True, write_only=True)
    password = serializers.CharField(required=True, write_only=True)
    # ==== OUTPUT ====
    refresh = serializers.CharField(read_only=True)


    def validate(self, attrs):
        # standard validation
        validated_data = super().validate(attrs)

        # validate email and password
        username = validated_data['username']
        password = validated_data['password']
        error_msg = _('username или password не корректны')
        try:
            user = UserModel.objects.get(username=username)
            if not user.check_password(password):
                raise serializers.ValidationError(error_msg)
            validated_data['user'] = user
        except UserModel.DoesNotExist:
            raise serializers.ValidationError(error_msg)

        return validated_data

    def create(self, validated_data):

        refresh_payload = {
            'iss': 'api_interface',
            'user_id': validated_data['user'].id,
            'exp': datetime.utcnow() + timedelta(seconds=JWT_REFRESH_TTL),
            'type': 'refresh'
        }
        refresh = jwt.encode(payload=refresh_payload, key=JWT_SECRET)
        # payload = jwt.decode(refresh, JWT_SECRET, algorithms=["HS256"])    #раскодирование токена
        # print(payload)

        return {
            'refresh': refresh
        }


# # ACCESS -- ЗДЕСЬ ЭТО КОРОТКИЙ(ПО ВРЕМЕНИ) ТОКЕН
# # REFRESH -- ЗДЕСЬ ЭТО ДЛИННЫЙ(ПО ВРЕМЕНИ ЖИЗНИ) ТОКЕН
# class RefreshSerializer(serializers.Serializer):
#     # ==== INPUT ====
#     refresh_token = serializers.CharField(required=True, write_only=True)
#     # ==== OUTPUT ====

#     refresh = serializers.CharField(read_only=True)

#     def validate(self, attrs):
#         # standard validation
#         validated_data = super().validate(attrs)

#         # validate refresh
#         refresh_token = validated_data['refresh_token']
#         try:
#             payload = jwt.decode(refresh_token, JWT_SECRET,  algorithms=["HS256"])
#             if payload['type'] != 'refresh':
#                 error_msg = {'refresh_token': _('Token type is not refresh!')}
#                 raise serializers.ValidationError(error_msg)
#             validated_data['payload'] = payload
#         except jwt.ExpiredSignatureError:
#             error_msg = {'refresh_token': _('Refresh token is expired!')}
#             raise serializers.ValidationError(error_msg)
#         except jwt.InvalidTokenError:
#             error_msg = {'refresh_token': _('Refresh token is invalid!')}
#             raise serializers.ValidationError(error_msg)

#         return validated_data

#     def create(self, validated_data):

#         refresh_payload = {
#             'iss': 'api_interface',
#             'user_id': validated_data['payload']['user_id'],
#             'exp': datetime.utcnow() + timedelta(seconds=JWT_REFRESH_TTL),
#             'type': 'refresh'
#         }
#         refresh = jwt.encode(payload=refresh_payload, key=JWT_SECRET)

#         return {
#             'refresh': refresh
#         }