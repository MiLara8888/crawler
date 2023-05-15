#!/usr/bin/env python
# -- coding: utf-8 --
"""
"""
#импорты стандартных библиотек
import json
from datetime import datetime

import logging
from logging import INFO, WARNING, ERROR, CRITICAL, FileHandler

from django.http.request import HttpRequest
from django.db.utils import IntegrityError
from django.db.transaction import TransactionManagementError
from django.core.exceptions import ObjectDoesNotExist, FieldError
from django.db import transaction, DatabaseError, OperationalError, IntegrityError, Error
from django.http import JsonResponse

from rest_framework.viewsets import ViewSet
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.status import HTTP_500_INTERNAL_SERVER_ERROR, HTTP_201_CREATED, HTTP_400_BAD_REQUEST, HTTP_200_OK, HTTP_404_NOT_FOUND
from rest_framework.exceptions import ValidationError
from rest_framework.renderers import JSONRenderer, BaseRenderer
from rest_framework_xml.renderers import XMLRenderer
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import renderers
from rest_framework.renderers import BaseRenderer
from rest_framework.permissions import AllowAny, IsAuthenticated
import xml.etree.ElementTree as ET

#импорты сторонних библиотек
import jwt
import io



#импорты модулей текущего проекта
from urlopen_app.models import Site, Page, Item, User
from api_interface.serializers import SiteSerializer, ItemSerializer, LoginSerializer
from urlopen_app.renderers import UserJSONRenderer
from urlopen_app.edt import ChoicesStatus, ChoicesPage
from api_interface.xml_fabric import XmlRendererSite, XmlRendererItem, XmlRendererError
# from api_interface.exceptions import exception_handler


#настройки логгирования
# log_format = '%(asctime)s   - %(name)s - %(levelname)s - %(message)s'
# logger = logging.getLogger('api_interface')
# logger.setLevel(logging.INFO)  # уровень на уровне всего логирования файла
# class DebugFileHandler(FileHandler):
#     """
#     переопределение класса, чтобы warning и info падали в другой файл
#     """
#     def __init__(self, filename: str, mode='a', encoding=None, delay=False):
#         super().__init__(filename, mode, encoding, delay)

#     def emit(self, record):
#         if record.levelno == CRITICAL or record.levelno == ERROR or record.levelno == WARNING:
#             return
#         super().emit(record)

# info_handler = DebugFileHandler('log/api_interface_info.log')
# info_handler.setLevel(logging.INFO)
# info_handler.setFormatter(logging.Formatter(log_format))
# logger.addHandler(info_handler)
# error_handler = logging.FileHandler('log/api_interface_error.log')
# error_handler.setLevel(logging.WARNING)
# error_handler.setFormatter(logging.Formatter(log_format))
# logger.addHandler(error_handler)


class NonTypeof(Exception):
    """если тип передан не верно """
    pass

class EmptyRecords(Exception):
    """Вызовется при пустом records"""
    pass

class Double(Exception):
    pass


#1 создать декоратор try catch с обработкой ошибок
#2 создать класс с фабричным методом
# ошибки с возвращением типа


class XMLRenderer(BaseRenderer):
    """кастомный xml renderer"""
    media_type = "application/xml"
    format = "xml"
    charset = "utf-8"

    def render(self, data, accepted_media_type=None, renderer_context=None):
        return data.getvalue().decode(encoding="utf-8")


# def dict_to_typeof(dict_data, typeof: str='xml', status = HTTP_404_NOT_FOUND):
#     """функция для создания из dict-ответа xml-ответ"""
#     resp = Response({'error':'ошибка'}, status=status)
#     if typeof=='xml':
#         n = XMLRenderer()
#         xml_data = dicttoxml(dict_data, custom_root='data', attr_type=False)
#         resp = Response(n.render(io.BytesIO(xml_data)), status=HTTP_200_OK)
#         resp.content = resp.data
#         resp.headers['Content-Type'] = 'application/xml; charset=utf-8'
#         return resp
#     elif typeof=='json':
#         resp = Response(dict_data, status=HTTP_200_OK)
#     else:
#         resp = Response({'error':'запрос может быть только в xml или json формате'}, status=HTTP_400_BAD_REQUEST)
#     return resp


class CustomResponce:
    """класс для формирования sql запроса возвращающий либо query.RawQuerySet либо ошибки"""
    # renderer_classes = ( JSONRenderer, XMLRenderer, )
    model = None
    sql_raw: str = None
    typeof: str = None
    many: bool = None
    resp: Response = None
    records = None
    json_serializer = None
    xml_renderer = None
    list_args: list =[]


    def __init__(self, model=None, sql_raw: str=None, typeof='xml', many=False, json_serializer=None, xml_renderer=None) -> None:
        self.model = model    #модель для которой будет производиться sql запрос
        self.sql_raw = sql_raw    #sql запрос
        self.typeof = typeof    #тип запроса передаваемый в url
        self.many = many    #данные для json сериалайзера о том, множественные ли данные будет идти в сериалайзер
        self.resp = Response()    #объект Response() возвращаемый из класса
        self.records = None   #данные полученые из sql запроса
        self.json_serializer = json_serializer    #класс сериалайзера для обработки данных json
        self.xml_renderer = xml_renderer    #класс для обработки данных xml
        self.list_args = None    #данные из url уточныющие sql запрос


    def db_exception_decorator(fn):
        """декоратор основной"""
        def wrapped(self, *args, **kwargs ):
            try:
                return fn(self, *args, **kwargs)
            except NonTypeof as e:
                string_type = self.typeof
                self.typeof = 'xml'
                # logger.error(f"{e} ошибка None Typeof на данных {string_type}")
                return self.error_resp(e, f'Ошибка в написании формата получаемых данных - {string_type}. Данные могут быть получены в json или xml форматах', HTTP_404_NOT_FOUND )
            except EmptyRecords as e:
                # logger.error(f"{e} Данные отсутствуют {self.sql_raw} на данных {self.list_args}")
                return self.error_resp(e, f'Данные отсутствуют', HTTP_404_NOT_FOUND )
            except DatabaseError as e:
                # logger.error(f'{e} Произошла ошибка в бд с запросом {self.sql_raw} -- {self.list_args}')
                return self.error_resp(e, 'Ошибка базы данных' , HTTP_500_INTERNAL_SERVER_ERROR)
            except AttributeError as e:
                # logger.error(e, f"{e} ошибка AttributeError на данных {self.sql_raw} -- {self.list_args}")
                return self.error_resp(e, 'Ошибка', HTTP_500_INTERNAL_SERVER_ERROR)
            except ObjectDoesNotExist as e:
                # logger.error(f"{e} ошибка ObjectDoesNotExist на данных {self.sql_raw} -- {self.list_args}")
                return self.error_resp(e, 'Ошибка базы данных', HTTP_500_INTERNAL_SERVER_ERROR)
            except FieldError as e:
                # logger.error(f"{e} ошибка FieldError на данных {self.sql_raw} -- {self.list_args}")
                return self.error_resp(e, 'Ошибка базы данных', HTTP_500_INTERNAL_SERVER_ERROR)
            except Error as e:
                # logger.error(f"{e} ошибка Error на данных {self.sql_raw} -- {self.list_args}")
                return self.error_resp(e, 'Ошибка', HTTP_500_INTERNAL_SERVER_ERROR)
            except Exception as e:
                # logger.error(f"{e} ошибка Exception на данных {self.sql_raw} -- {self.list_args}")
                return self.error_resp(e, 'Ошибка', HTTP_500_INTERNAL_SERVER_ERROR)
        return wrapped


    @db_exception_decorator
    def sql_request(self, *args):
        self.list_args = args   #аргументы необходимые для запроса
        self.records = self.model.objects.raw(self.sql_raw, *args)    #получение данных из запроса, ошибки обрабатываются в обёртке декораторе

        if self.typeof not in ['xml', 'json']:
            # logger.error(f'Был запрошен формат {self.typeof} и вызвана ошибка NoneTypeof')
            raise NonTypeof    #если формат недопустимый

        if not self.records:
            # logger.error(f'Клиет получил ошибку по пустому records запрос{self.sql_raw}{args} и вызов ошибки EmptyRecords')
            raise EmptyRecords    #если данных в records по какой-то причине нет

        #далее при определении формата переходим в обрабатывющий этот формат службу описаную в классе, при жедании в эти службы можно добавлять разные типы данных
        #сейчас описаны xml и json
        if self.typeof=='xml':
            return self._ToXml()

        elif self.typeof=='json':
            return self._ToJson()


    def _ToJson(self):
        if self.many==False:
            self.records = self.records[0]
        serializer = self.json_serializer(self.records, many=self.many)  #формирование объекта для передачи
        self.resp = Response(serializer.data, HTTP_200_OK)
        self.resp.headers['Content-Type'] = 'application/json; charset=utf-8'
        return self.resp


    def _ToXml(self):
        n = XMLRenderer()
        xml_data = self.xml_renderer(self.records)
        xml_data = xml_data.formation_xml()
        self.resp = Response(n.render(xml_data), status=HTTP_200_OK)
        self.resp.content = self.resp.data
        self.resp.headers['Content-Type'] = 'application/xml; charset=utf-8'
        return self.resp


    def error_resp(self, error, message='Ошибка', status=HTTP_400_BAD_REQUEST):
        error_dict = {'error': message}
        if self.typeof=='xml':
            n = XMLRenderer()
            xml_data = XmlRendererError(error_dict)
            xml_data = xml_data.formation_xml()
            self.resp = Response(n.render(xml_data), status=status)
            self.resp.content = self.resp.data
            self.resp.headers['Content-Type'] = 'application/xml; charset=utf-8'
            return self.resp
        elif self.typeof=='json':
            # print(error)    #это в логи себе закинуть TODO
            self.resp = JsonResponse(error_dict, status=status)
            self.resp.headers['Content-Type'] = 'application/json; charset=utf-8'
            return self.resp


# class LoginView(APIView):

#     def post(self, request, format=None):
#         serializer = LoginSerializer(data=request.data)
#         if serializer.is_valid():
#             response_data = serializer.save()
#             # print(type(response_data))
#             jsonStr = json.dumps(response_data)
#             return Response(response_data, status=HTTP_200_OK)

#         return Response(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ApiInterfaceTokenViewSet(ViewSet):
    read_only = True
    renderer_classes = ( JSONRenderer, XMLRenderer, )
    permission_classes = (AllowAny,)
    responce = Response()

    # <?xml version="1.0" encoding="UTF-8" ?>
    #     <data>
    #         <username>lara2</username>
    #         <password>onotole88</password>
    #     </data>

    # def autorization_get_token(self, request: HttpRequest, typeof: str, *args, **kwargs):
    #     """передача от пользователя в post запросе username и пароль и получение токена в ответе
    #         в json или xml форматах
    #         django parser преобразует xml в json"""
    #     serializer = LoginSerializer(data=request.data)
    #     if serializer.is_valid():
    #         response_data = serializer.save()
    #         result =  dict_to_typeof(response_data, typeof=typeof, status=HTTP_200_OK)
    #         return result
    #     result = dict_to_typeof({'error':'Запрос некорректный'}, typeof=typeof, status=HTTP_400_BAD_REQUEST)
    #     return result


    # def refresh_token(self, request: HttpRequest, typeof: str, *args, **kwargs):
    #     serializer = RefreshSerializer(data=request.data)
    #     if serializer.is_valid():
    #         response_data = serializer.save()
    #         return Response(response_data)

    #     return Response(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)



class ApiInterfaceViewSet(ViewSet):
    read_only = True
    renderer_classes = ( JSONRenderer, XMLRenderer, )
    # parser_classes = (IsAuthenticated, )
    responce = Response()


    def item_info(self, request: HttpRequest, typeof: str, domain_name: str, id: int, *args, **kwargs) -> Response:
        #<str:typeof>/site/<str:domain_name>/item/<int:id>'
        raw_sql :str = """select * from urlopen_app_item uai where id = %s"""    #получение объекта из бд
        obj = CustomResponce(model=Item, sql_raw=raw_sql, typeof=typeof, many=False, json_serializer=ItemSerializer, xml_renderer=XmlRendererItem)
        responce = obj.sql_request([id])
        return responce


    def items_info(self, request: HttpRequest, typeof: str, domain_name: str, against: int, count: int, *args, **kwargs) -> Response:
        #'<str:typeof>/site/<str:domain_name>/items/count
        # <int:against>/<int:count>
        raw_sql: str= """select uai.id, uai.name, uai.vendor_code, uai.sales_price, uai.time_update, uai.site_code
                        from urlopen_app_item uai
                        where uai.site_id = (select uas.id from urlopen_app_site uas where uas.domain_name = %s) and uai.vendor_code notnull
                        order by uai.id
                        limit %s offset %s"""    #sql запрос к базе данных
        obj = CustomResponce(Item, sql_raw=raw_sql, typeof=typeof, many=True, json_serializer=ItemSerializer, xml_renderer=XmlRendererItem)   #объект класса для создания кастомного респонса
        #передача модели для запроса, самого запроса, типа запроса получаемого из url по умолчанию это 'xml', параметра many для json сериалайзера, сам json сериалайзер и кастомную xml фабрику
        responce = obj.sql_request([domain_name, count+1, against])    #выполнение sql запроса и передача в запрос необходимых параметров
        return responce


    def site_info(self, request: HttpRequest, typeof: str, domain_name: str, *args, **kwargs) -> Response:
        #<str:typeof>/site/<str:domain_name>
        raw_sql :str= """select * from urlopen_app_site uas where  uas.domain_name = %s"""
        obj = CustomResponce(Site, sql_raw=raw_sql, typeof=typeof, many=False, json_serializer=SiteSerializer, xml_renderer=XmlRendererSite)
        responce = obj.sql_request([domain_name])
        return responce


    def sites_info(self, request: HttpRequest, typeof: str, against: int, count: int, *args, **kwargs) -> Response:
        #<str:typeof>/site/<int:against>/<int:count>
        raw_sql :str= """select * from urlopen_app_site uas limit %s offset %s"""
        obj = CustomResponce(Site, sql_raw=raw_sql, typeof=typeof, many=True, json_serializer=SiteSerializer, xml_renderer=XmlRendererSite)
        responce = obj.sql_request([count+1, against])
        return responce