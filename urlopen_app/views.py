#!/usr/bin/env python
# -- coding: utf-8 --
"""
"""
import json
from datetime import datetime

from django.http.request import HttpRequest
from django.db.utils import IntegrityError
from django.db.transaction import TransactionManagementError
from django.core.exceptions import ObjectDoesNotExist, FieldError
from django.db import transaction, DatabaseError, OperationalError, IntegrityError, Error
from django.http import JsonResponse

import logging
from logging import INFO, WARNING, ERROR, CRITICAL, FileHandler

from rest_framework.viewsets import ViewSet
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.status import HTTP_500_INTERNAL_SERVER_ERROR, HTTP_201_CREATED, HTTP_400_BAD_REQUEST, HTTP_200_OK, HTTP_404_NOT_FOUND
from rest_framework.views import APIView
from rest_framework.exceptions import ValidationError
from rest_framework.renderers import JSONRenderer, BaseRenderer
# from rest_framework_xml.renderers import XMLRenderer
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import renderers

from urlopen_app.models import Site, Page, Item
from urlopen_app.serializers import (GetHtmlSerialiser, LoaderNextSerializer,
                                     LoginSerializer, ParserPostSerializer,
                                     DictTypeSerializer, PostItemSerializer,
                                     AttemptSerializer, PictureUrlSerializer,
                                     ImageDecodeSerializer, DecodeSerializer)
from urlopen_app.renderers import UserJSONRenderer
from urlopen_app.edt import ChoicesStatus, ChoicesPage
from rest_framework.renderers import BaseRenderer



# #настройки логгирования
# log_format = '%(asctime)s   - %(name)s - %(levelname)s - %(message)s'
# logger = logging.getLogger('urlopen_app')
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

# info_handler = DebugFileHandler('log/urlopen-info.log')
# info_handler.setLevel(logging.INFO)
# info_handler.setFormatter(logging.Formatter(log_format))
# logger.addHandler(info_handler)
# error_handler = logging.FileHandler('log/urlopen-error.log')
# error_handler.setLevel(logging.WARNING)
# error_handler.setFormatter(logging.Formatter(log_format))
# logger.addHandler(error_handler)
# # logger.info('Драйвер инициализировался')


class NonVendorCode(Exception):
    pass


class Double(Exception):
    pass


class ControlerViewSet(ViewSet):
    """ Супер класс преставления """
    permission_classes = (AllowAny,)
    renderer_classes = (JSONRenderer, )
    read_only = True



    def change_status(self, records: list, status: ChoicesStatus, *args,
                      **kwargs):
        """изменение статуса"""
        if records:
            for i in records:
                i.status = status  #лучше не трогать метод save и метод update. они переопределены
                i.save()


#____________________________________________________________

    def get_next_urls(self, request: HttpRequest, cnt: int,  *args, **kwargs):
        """возвращает следующие cnt объектов в лоадер для извлечения html
            loader/nexturl/<int:cnt>/"""
        records = None
        try:
            with transaction.atomic():    #тут оставит статус 20 <html страницы не извлекался> если не сможет обработаться вернуть и изменить статус в бд

                # records = Page.objects.filter(status=ChoicesStatus.NOT_PROCESSED_HTML).order_by('time_update')[:cnt]    #получение объектов из бд

                records = Page.objects.raw("""SELECT uap.id, uap.time_create, uap.time_update, uap.url
                                            FROM urlopen_app_page as uap
                                            WHERE uap.status = %s
                                            ORDER BY uap.time_update
                                            LIMIT %s""", [ChoicesStatus.NOT_PROCESSED_HTML, cnt])

                #records = Page.objects.raw("""select uap.id, uap.time_create, uap.time_update, uap.url     #запрос включающий в себя обновление страниц раз в три дня
                                            # from urlopen_app_page uap
                                            # where status=%s or (status = %s and DATE_PART('day', CURRENT_TIMESTAMP-uap.time_update)>3)
                                            # order by status desc , uap.time_update
                                            # limit %s""", [ChoicesStatus.NOT_PROCESSED_HTML, SUCCESSFULLY_IMAGE_URL, cnt])



                serializer = LoaderNextSerializer(records, many=True)    #формирование объекта для передачи
                self.change_status(records, ChoicesStatus.IN_PROCESS_HTML)    #изменение статуса объекту
                return Response(serializer.data, status=HTTP_201_CREATED)

        except TransactionManagementError as e:    # поднимается для любых и всех проблем, связанных с транзакциями базы данных.
            return Response(f'{str(e)} ошибка транзакции {records}', status=HTTP_500_INTERNAL_SERVER_ERROR)

        except OperationalError as e:    #Операционная ошибка
            return Response(f'{str(e)} ошибка сохранения в базу {records}', status=HTTP_500_INTERNAL_SERVER_ERROR)

        except DatabaseError as e:    #ловим ошибки бд
            return Response(f'{str(e)} Ошибка в бд на get запросе', status=HTTP_500_INTERNAL_SERVER_ERROR)

        except FieldError as e:    #Исключение FieldError вызывается, если существует проблема с полем модели.
            return Response(f'{str(e)} ошибка в запрашиваемых полях {records}', status=HTTP_500_INTERNAL_SERVER_ERROR)

        except Error as e:    #общая для баз данных
            return Response(f'{str(e)} ошибка бд {records}', status=HTTP_500_INTERNAL_SERVER_ERROR)

        except Exception as e:
            return Response(str(e), status=HTTP_500_INTERNAL_SERVER_ERROR)


    def put_html(self, request: HttpRequest, pk: int, *args, **kwargs):
        """put запрос для добавления html по url
            puthtml/<int:pk>/"""
        try:
            with transaction.atomic():
                # snippet = Page.objects.get(pk=pk)
                snippet = Page.objects.raw(f'''SELECT uap.id, uap.time_update, uap.time_create
                                            FROM urlopen_app_page as uap
                                            WHERE uap.id = %s''', [pk])[0]
                serializer = GetHtmlSerialiser(snippet, data=request.data)
                if serializer.is_valid(raise_exception=True):
                    serializer.save()
                    return Response(status=HTTP_201_CREATED)

        except TransactionManagementError as e:    # поднимается для любых и всех проблем, связанных с транзакциями базы данных.
            return Response(f'{str(e)} ошибка транзакции {snippet.pk}', status=HTTP_500_INTERNAL_SERVER_ERROR)

        except DatabaseError as e:    #ловим ошибки бд
            snippet = Page.objects.get(pk=pk)
            snippet.status = ChoicesStatus.NOT_PROCESSED_HTML
            snippet.save()
            return Response(f'{str(e)} Ошибка в бд', status=HTTP_500_INTERNAL_SERVER_ERROR)

        except ObjectDoesNotExist as e:    #если нету snippet по pk в бд
            return Response(f'Элемент с id-{pk} не найден в бд', status=HTTP_500_INTERNAL_SERVER_ERROR)

        except FieldError as e:    #Исключение FieldError вызывается, если существует проблема с полем модели.
            return Response(f'{str(e)} ошибка в запрашиваемых полях {pk}', status=HTTP_500_INTERNAL_SERVER_ERROR)

        except ValidationError as e:
            snippet = Page.objects.get(pk=pk)
            snippet.status = ChoicesStatus.ERROR_VALIID_HTML
            snippet.save()
            return Response(f'Ошибка валидации, объекту {snippet.pk}', status=HTTP_500_INTERNAL_SERVER_ERROR)

        except Error as e:    #Основная для ошибок связанных с бд
            snippet = Page.objects.get(pk=pk)
            snippet.status = ChoicesStatus.NOT_PROCESSED_HTML
            snippet.save()
            return Response(f'Ошибка в бд {str(e)}', status=HTTP_500_INTERNAL_SERVER_ERROR)

        except ConnectionError  as e:    #Базовый класс для проблем, связанных с подключением.
            snippet = Page.objects.get(pk=pk)
            snippet.status = ChoicesStatus.NOT_PROCESSED_HTML
            snippet.save()
            return Response(f'{str(e)} Проблемы с подключением', status=HTTP_500_INTERNAL_SERVER_ERROR)

        except Exception as e:
            snippet = Page.objects.get(pk=pk)
            snippet.status = ChoicesStatus.NOT_PROCESSED_HTML
            snippet.save()
            return Response(str(e), status=HTTP_500_INTERNAL_SERVER_ERROR)

#____________________________________________________________

    def get_next_html(self, request: HttpRequest, cnt: int,  *args, **kwargs):
        """возвращает следующие cnt объектов html для извлечения url-ок
            parser/give-html/<int:cnt>/"""
        try:
            with transaction.atomic():    #тут оставит статус 30 < 'HTML успешно извлечён страница готова к извлечению url-ок'>
                # records = Page.objects.filter(status=ChoicesStatus.HTML_SUCCESSFULLY).order_by('-time_update')[:cnt]
                records = Page.objects.raw("""SELECT uap.id, uap.time_create, uap.time_update, uap.html_page, uap.url
                                            FROM urlopen_app_page as uap
                                            WHERE uap.status = %s
                                            ORDER BY uap.time_update
                                            LIMIT %s""", [ChoicesStatus.HTML_SUCCESSFULLY, cnt])
                serializer = LoaderNextSerializer(records, many=True)
                self.change_status(records, ChoicesStatus.IN_PROCESS_PARS)
                return Response(serializer.data, status=HTTP_201_CREATED)

        except TransactionManagementError as e:    # поднимается для любых и всех проблем, связанных с транзакциями базы данных.
            return Response(f'{str(e)} ошибка транзакции {records}', status=HTTP_500_INTERNAL_SERVER_ERROR)

        except OperationalError as e:    #Операционная ошибка
            return Response(f'{str(e)} ошибка сохранения в базу {records}', status=HTTP_500_INTERNAL_SERVER_ERROR)

        except DatabaseError as e:    #ловим ошибки бд
            return Response(f'{str(e)} Ошибка в бд на get запросе', status=HTTP_500_INTERNAL_SERVER_ERROR)

        except FieldError as e:
            return Response(f'{str(e)} ошибка в запрашиваемых полях {records}', status=HTTP_500_INTERNAL_SERVER_ERROR)

        except Error as e:    #общая для баз данных
            return Response(f'{str(e)} ошибка бд {records}', status=HTTP_500_INTERNAL_SERVER_ERROR)

        except Exception as e:
            return Response(str(e), status=HTTP_500_INTERNAL_SERVER_ERROR)


    def post_url(self, request: HttpRequest, site_pk: int, page_pk: int, *args, **kwargs):
        """ post запрос для добавления url-ok в бд
        обрабатывает пришедшие url-ки
        parser/posturl/<int:site_pk>/<int:page_pk>/"""
        try:
            snippet = Page.objects.get(pk=page_pk)    #страница с которой url
            # raise DatabaseError
            site = Site.objects.get(pk=site_pk)    #сайт страницы
            serializer = ParserPostSerializer(data=request.data)
            if serializer.is_valid(raise_exception=True):
                with transaction.atomic():
                    data = serializer.validated_data    #url-ки
                    snippet.status = data.get('status',ChoicesStatus.HTML_SUCCESSFULLY)
                    if snippet.status==93:
                        snippet.html_page = ''
                    snippet.save()
                    list_url = data.get('url_list',[])
                    for url in list_url:
                        try:
                            page = Page.objects.get(site=site, url=url)
                        except Page.DoesNotExist as e:
                            page = Page()
                            page.site_id = site.id
                            page.url = url
                            page.save()
                    return Response(status=HTTP_201_CREATED)

        # except ObjectDoesNotExist as e:    #если нету snippet по pk в бд
        #     return Response(f'Элемент с id-{page_pk} не найден в бд', status=HTTP_500_INTERNAL_SERVER_ERROR)

        except TransactionManagementError as e:    # поднимается для любых и всех проблем, связанных с транзакциями базы данных.
            return Response(f'{str(e)} ошибка транзакции {page_pk}', status=HTTP_500_INTERNAL_SERVER_ERROR)    #TODO убери snippet

        except DatabaseError as e:    #ловим ошибки бд
            snippet = Page.objects.get(pk=page_pk)
            snippet.status = ChoicesStatus.HTML_SUCCESSFULLY
            snippet.save()
            return Response(f'{str(e)} Ошибка в бд', status=HTTP_500_INTERNAL_SERVER_ERROR)

        except FieldError as e:    #Исключение FieldError вызывается, если существует проблема с полем модели.
            return Response(f'{str(e)} ошибка в запрашиваемых полях {page_pk}', status=HTTP_500_INTERNAL_SERVER_ERROR)

        except ValidationError as e:
            snippet.status = ChoicesStatus.ERROR_URL_PARSE  # "Ошибка валидации post запроса с url"
            snippet.save()
            return Response('Произошла проблема с валидацией сериалайзера', status=HTTP_500_INTERNAL_SERVER_ERROR)

        except Error as e:    #Основная для ошибок связанных с бд
            snippet.status = ChoicesStatus.HTML_SUCCESSFULLY  # "Ошибка валидации post запроса с url"
            snippet.save()
            return Response(f'Ошибка в бд {str(e)}', status=HTTP_500_INTERNAL_SERVER_ERROR)

        except ConnectionError  as e:
            return Response(str(e), status=HTTP_500_INTERNAL_SERVER_ERROR)

        except Exception as e:
            snippet = Page.objects.get(pk=page_pk)
            snippet.status = ChoicesStatus.HTML_SUCCESSFULLY
            snippet.save()
            return Response(str(e), status=HTTP_500_INTERNAL_SERVER_ERROR)

#_________________________________________________________________


    def get_url_category(self, request: HttpRequest, cnt: int, *args, **kwargs):
        """возвращает следующие n страниц с неопределенным типом страницы
            parser/get-category-url/<int:cnt>/"""
        try:
            with transaction.atomic():
                # records = Page.objects.filter(status=ChoicesStatus.SUCCESSFULLY_URL).order_by('-time_update')[:cnt]
                records = Page.objects.raw("""SELECT uap.id, uap.time_create, uap.time_update, uap.url
                                            FROM urlopen_app_page as uap
                                            WHERE uap.status = %s
                                            ORDER BY uap.time_update
                                            LIMIT %s""", [ChoicesStatus.SUCCESSFULLY_URL, cnt])
                serializer = LoaderNextSerializer(records, many=True)
                self.change_status(records, ChoicesStatus.IN_PROCESS_TYPE)
                return Response(serializer.data, status=HTTP_201_CREATED)

        except TransactionManagementError as e:    # поднимается для любых и всех проблем, связанных с транзакциями базы данных.
            return Response(f'{str(e)} ошибка транзакции {records}', status=HTTP_500_INTERNAL_SERVER_ERROR)

        except OperationalError as e:    #Операционная ошибка
            return Response(f'{str(e)} ошибка сохранения в базу {records}', status=HTTP_500_INTERNAL_SERVER_ERROR)

        except DatabaseError as e:    #ловим ошибки бд
            return Response(f'{str(e)} Ошибка в бд на get запросе', status=HTTP_500_INTERNAL_SERVER_ERROR)

        except FieldError as e:
            return Response(f'{str(e)} ошибка в запрашиваемых полях {records}', status=HTTP_500_INTERNAL_SERVER_ERROR)

        except Error as e:    #общая для баз данных
            return Response(f'{str(e)} ошибка бд {records}', status=HTTP_500_INTERNAL_SERVER_ERROR)

        except Exception as e:
            return Response(str(e), status=HTTP_500_INTERNAL_SERVER_ERROR)


    def post_category(self, request: HttpRequest, *args, **kwargs):
        """для получения массива с новыми типами страницы
            массив вида  [[id,тип страницы],[id,тип страницы]]
            parser/postcategory/
        """
        serializer = DictTypeSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
                data = serializer.validated_data
                result_list = data.get('result_list',[])
        else:
            raise ValidationError
        try:
            with transaction.atomic():
                for i in result_list:
                    """сохраняет тип страницы"""
                    page_pk = i[0]    #id
                    page_type = i[1]    #тип
                    page = Page.objects.raw(f'''SELECT uap.id, uap.time_update, uap.time_create
                                            FROM urlopen_app_page as uap
                                            WHERE uap.id = %s''', [page_pk])[0]
                    # page = Page.objects.get(pk=page_pk)
                    page.type_page = page_type
                    page.status = ChoicesStatus.SUCCESSFULLY_TYPE    #'Тип страницы успешно определён, страница готова к отправке на фабрику'
                    if page_type not in [10, 20]:    #очищаем html-ку если тип страницы не продукт и не страница бренда
                        page.html_page = ''
                    page.save()
            return Response(status=HTTP_201_CREATED)

        except IndexError as e:
            return Response(f'Не корректно переданы данные {e}', status=HTTP_500_INTERNAL_SERVER_ERROR)

        except TransactionManagementError as e:    # поднимается для любых и всех проблем, связанных с транзакциями базы данных.
            for i in result_list:
                page_pk = i[0]    #id
                page_type = i[1]    #тип
                page = Page.objects.get(pk=page_pk)
                page.status = ChoicesStatus.SUCCESSFULLY_URL    #'Из страницы успешно извлечены url страница готова к определению типа
                page.save()
            return Response(f'{str(e)} ошибка транзакции', status=HTTP_500_INTERNAL_SERVER_ERROR)

        except DatabaseError as e:    #ловим ошибки бд
            for i in result_list:
                page_pk = i[0]    #id
                page_type = i[1]    #тип
                page = Page.objects.get(pk=page_pk)
                page.status = ChoicesStatus.SUCCESSFULLY_URL    #'Из страницы успешно извлечены url страница готова к определению типа
                page.save()
            return Response(f'{str(e)} Ошибка в бд', status=HTTP_500_INTERNAL_SERVER_ERROR)

        except AttributeError as e:
            return Response(f'Не корректно переданы данные {e}', status=HTTP_500_INTERNAL_SERVER_ERROR)

        except ObjectDoesNotExist as e:    #если нету snippet по pk в бд
            return Response(f'Элемент не найден в бд', status=HTTP_500_INTERNAL_SERVER_ERROR)

        except FieldError as e:    #Исключение FieldError вызывается, если существует проблема с полем модели.
            return Response(f'{str(e)} ошибка в запрашиваемых полях ', status=HTTP_500_INTERNAL_SERVER_ERROR)

        except ValidationError as e:
            return Response(f'Ошибка валидации {serializer}', status=HTTP_500_INTERNAL_SERVER_ERROR)

        except Error as e:    #Основная для ошибок связанных с бд
            for i in result_list:
                page_pk = i[0]    #id
                page_type = i[1]    #тип
                page = Page.objects.get(pk=page_pk)
                page.status = ChoicesStatus.SUCCESSFULLY_URL    #'Из страницы успешно извлечены url страница готова к определению типа
                page.save()
            return Response(f'Ошибка в бд {str(e)}', status=HTTP_500_INTERNAL_SERVER_ERROR)

        except ConnectionError  as e:    #Базовый класс для проблем, связанных с подключением.
            return Response(f'{str(e)} Проблемы с подключением', status=HTTP_500_INTERNAL_SERVER_ERROR)

        except Exception as e:
            for i in result_list:
                page_pk = i[0]    #id
                page_type = i[1]    #тип
                page = Page.objects.get(pk=page_pk)
                page.status = ChoicesStatus.SUCCESSFULLY_URL    #'Из страницы успешно извлечены url страница готова к определению типа
                page.save()
            return Response(str(e), status=HTTP_500_INTERNAL_SERVER_ERROR)

#____________________________________________________________________

    def get_next_html_factory(self, request: HttpRequest, cnt: int, *args, **kwargs):
        """возвращает следубщие n страниц c типом страницы <продукты>
            factory/give-html/<int:cnt>/"""
        try:
            with transaction.atomic():
                # records = Page.objects.filter(type_page=ChoicesPage.ITEM, status=ChoicesStatus.SUCCESSFULLY_TYPE).order_by('-time_update')[:cnt]  # продукт со статусом <Тип страницы успешно определён, страница готова к отправке на фабрику>
                records = Page.objects.raw("""SELECT uap.id, uap.time_create, uap.time_update, uap.url, uap.html_page
                                            FROM urlopen_app_page as uap
                                            WHERE uap.status = %s and uap.type_page = %s
                                            ORDER BY uap.time_update desc
                                            LIMIT %s""", [ChoicesStatus.SUCCESSFULLY_TYPE, ChoicesPage.ITEM, cnt])
                # for i in records:
                #     print(i.url)
                #     print(i.image_item)
                serializer = LoaderNextSerializer(records, many=True)
                self.change_status(records, ChoicesStatus.FACTORY_VISIT)
                return Response(serializer.data, status=HTTP_201_CREATED)

        except TransactionManagementError as e:    # поднимается для любых и всех проблем, связанных с транзакциями базы данных.
            return Response(f'{str(e)} ошибка транзакции {records}', status=HTTP_500_INTERNAL_SERVER_ERROR)

        except OperationalError as e:    #Операционная ошибка
            return Response(f'{str(e)} ошибка сохранения в базу {records}', status=HTTP_500_INTERNAL_SERVER_ERROR)

        except DatabaseError as e:    #ловим ошибки бд
            return Response(f'{str(e)} Ошибка в бд на get запросе', status=HTTP_500_INTERNAL_SERVER_ERROR)

        except FieldError as e:
            return Response(f'{str(e)} ошибка в запрашиваемых полях {records}', status=HTTP_500_INTERNAL_SERVER_ERROR)

        except Error as e:    #общая для баз данных
            return Response(f'{str(e)} ошибка бд {records}', status=HTTP_500_INTERNAL_SERVER_ERROR)

        except Exception as e:
            return Response(str(e), status=HTTP_500_INTERNAL_SERVER_ERROR)



    def post_item(self, request: HttpRequest,  site_pk: int, page_pk: int, *args, **kwargs):
        """получаем информацию о товаре по post запросу добавление item в бд по site_pk
            factory/post-item/<int:site_pk>/<int:page_pk>/
        """
        try:
            # page = Page.objects.get(pk=page_pk)
            page = Page.objects.raw(f'''SELECT *
                                            FROM urlopen_app_page as uap
                                            WHERE uap.id = %s''', [page_pk])[0]
            site = Site.objects.get(pk=site_pk)
            serializer = PostItemSerializer(data=request.data)
            if serializer.is_valid(raise_exception=True):
                with transaction.atomic():
                    data = serializer.validated_data
                    name = data.get('name', None)
                    vendor_code = data.get('vendor_code', None)
                    unit = data.get('unit', None)
                    wholesale_price = data.get('wholesale_price', None)
                    sales_price = data.get('sales_price', None)
                    site_code = data.get('site_code', None)
                    brand = data.get('brand', None)
                    json_data = data.get('json_data', None)
                    if page.image_item:     #если в уже есть связанный товар то обновляем
                        # try:    #TODO убрать и избавиться от проблем дублирования этих данных
                        #     item = Item.objects.get(pk=page.image_item)
                        # except Exception as e:
                        #     return Response(f'{str(e)} TODO ошибка дублирования в гет запросе', status=HTTP_500_INTERNAL_SERVER_ERROR)
                        item = page.image_item
                        item.name = name
                        item.vendor_code = vendor_code
                        item.unit = unit
                        item.wholesale_price = wholesale_price
                        item.sales_price = sales_price
                        item.site_code = site_code
                        item.brand = brand
                        item.json_data = json_data
                        item.page = page
                        item.site = site
                        item.save()
                    elif not page.image_item:
                        item = Item.objects.create(site=site, name=name, vendor_code=vendor_code, unit=unit, wholesale_price=wholesale_price,
                                                   page=page, json_data=json_data, brand=brand, site_code=site_code, sales_price=sales_price)
                        item.save()
                        page.image_item_id = item.id
                    #тут стоит проверить есть ли к этой с транице УЖЕ привязанные картинки, если они есть соотвественно то извлекать повторно их не надо,
                    #сайты могут менять текст ссылок на картинки и мы получим дубли
                    #а если их нету то стоит извлечь картинки
                    picture_list = Page.objects.raw(f"""select id
                                                        from urlopen_app_page uap
                                                        where uap.image_page_id = %s""", [page_pk])
                    if picture_list:
                        page.status = ChoicesStatus.SUCCESSFULLY_IMAGE_URL    #URL картинок и товары успешно извлечены
                    if not picture_list:
                        page.status = ChoicesStatus.SUCCESSFULLY_ITEM   #Страница обработана, товар извлечён, готова к извлечению url-ok картинок товара
                    page.attempts = 0
                    page.save()
                    return Response(status=HTTP_201_CREATED)

        except IndexError as e:
            return Response(f'Не корректно переданы данные {e}', status=HTTP_500_INTERNAL_SERVER_ERROR)

        except AttributeError as e:
            return Response(f'Не корректно переданы данные {e}', status=HTTP_500_INTERNAL_SERVER_ERROR)

        except IntegrityError as e:
            # item = item.objects.get(name=name, vendor_code=vendor_code, site=site)
            # print(item.page)
            # print(page.id)
            page.status = ChoicesStatus.ERROR_UNIQUE
            page.save()
            return Response(f'{e} Такой объект уже присутствует в базе {page_pk}', status=HTTP_500_INTERNAL_SERVER_ERROR)

        except ObjectDoesNotExist as e:    #если нету snippet по pk в бд
            return Response(f'Элемент не найден в бд page - {page_pk} site - {site_pk}', status=HTTP_500_INTERNAL_SERVER_ERROR)

        except FieldError as e:    #Исключение FieldError вызывается, если существует проблема с полем модели.
            return Response(f'{str(e)} ошибка в запрашиваемых полях ', status=HTTP_500_INTERNAL_SERVER_ERROR)

        except TransactionManagementError as e:    # поднимается для любых и всех проблем, связанных с транзакциями базы данных.
            return Response(f'{str(e)} ошибка транзакции', status=HTTP_500_INTERNAL_SERVER_ERROR)

        except DatabaseError as e:    #ловим ошибки бд
            page = Page.objects.get(pk=page_pk)
            page.status = ChoicesStatus.SUCCESSFULLY_TYPE
            page.save()
            return Response(f'{str(e)} Ошибка в бд', status=HTTP_500_INTERNAL_SERVER_ERROR)

        except ValidationError as e:
            page = Page.objects.get(pk=page_pk)
            page.status = ChoicesStatus.ERROR_FACTORY_VALID  # "Ошибка валидации post запроса с url"
            page.save()
            return Response(f'Произошла проблема с валидацией сериалайзера {page_pk}', status=HTTP_500_INTERNAL_SERVER_ERROR)

        except ConnectionError  as e:    #Базовый класс для проблем, связанных с подключением.
            return Response(f'{str(e)} Проблемы с подключением', status=HTTP_500_INTERNAL_SERVER_ERROR)

        except Exception as e:
            page = Page.objects.get(pk=page_pk)
            page.status = ChoicesStatus.SUCCESSFULLY_TYPE
            page.save()
            return Response(str(e), status=HTTP_500_INTERNAL_SERVER_ERROR)

#_________________________________________________________________


    def get_extract_image(self, request: HttpRequest,  cnt: int, *args, **kwargs):
        """
        метод для отправки html для извлечения url картинок
        parser/get-picture-url/<int:cnt>/
        """
        try:
            with transaction.atomic():
                # records = Page.objects.filter(type_page=ChoicesPage.ITEM, status=ChoicesStatus.SUCCESSFULLY_ITEM).order_by('-time_update')[:cnt]
                records = Page.objects.raw("""SELECT uap.id, uap.time_create, uap.time_update, uap.url, uap.html_page
                                            FROM urlopen_app_page as uap
                                            WHERE uap.status = %s and uap.type_page = %s
                                            ORDER BY uap.time_update
                                            LIMIT %s""", [ChoicesStatus.SUCCESSFULLY_ITEM, ChoicesPage.ITEM, cnt])
                self.change_status(records, ChoicesStatus.IN_PROCESS_IMAGE)    #IN_PROCESS_IMAGE
                serializer = LoaderNextSerializer(records, many=True)
                return Response(serializer.data, status=HTTP_201_CREATED)


        except TransactionManagementError as e:    # поднимается для любых и всех проблем, связанных с транзакциями базы данных.
            return Response(f'{str(e)} ошибка транзакции {records}', status=HTTP_500_INTERNAL_SERVER_ERROR)

        except OperationalError as e:    #Операционная ошибка
            return Response(f'{str(e)} ошибка сохранения в базу {records}', status=HTTP_500_INTERNAL_SERVER_ERROR)

        except DatabaseError as e:    #ловим ошибки бд
            return Response(f'{str(e)} Ошибка в бд на get запросе', status=HTTP_500_INTERNAL_SERVER_ERROR)

        except FieldError as e:
            return Response(f'{str(e)} ошибка в запрашиваемых полях {records}', status=HTTP_500_INTERNAL_SERVER_ERROR)

        except Error as e:    #общая для баз данных
            return Response(f'{str(e)} ошибка бд {records}', status=HTTP_500_INTERNAL_SERVER_ERROR)

        except Exception as e:
            return Response(str(e), status=HTTP_500_INTERNAL_SERVER_ERROR)



    def post_picture_url(self, request:HttpRequest, site_pk: int, page_pk: int, *args, **kwargs):
        """ сохранение url картинок
            parser/post-picture-url/<int:site_pk>/<int:page_pk>/"""

        try:
            page_obj = Page.objects.raw(f'''SELECT uap.id, uap.time_update, uap.time_create
                                            FROM urlopen_app_page as uap
                                            WHERE uap.id = %s''', [page_pk])[0]

            site = Site.objects.get(pk=site_pk)  #сайт
            item = Item.objects.get(page=page_pk)  #связанная модель товара

            if not item.vendor_code:
                page_obj.status = ChoicesStatus.SUCCESSFULLY_ITEM_NOT_VENDOR_CODE
                page_obj.html_page = ''
                page_obj.save()
                raise NonVendorCode

            serializer = PictureUrlSerializer(data=request.data)
            if serializer.is_valid(raise_exception=True):
                with transaction.atomic():
                    data = serializer.validated_data
                    list_image = data.get('picture_list', [])    #list с юрлками

                    try:
                        start_num_count = Page.objects.filter(image_item=item).order_by('-image_counter').first().image_counter
                        if start_num_count==0:
                            start_num_count = 1
                    except Exception as e:
                        start_num_count = 1

                    for url in list_image:
                        try:
                            page = Page.objects.get(site=site, url=url)    #если уже есть проходим дальше
                        except Page.DoesNotExist as e:
                            page = Page()
                            page.image_counter = start_num_count
                            extension = url.split('.')[-1]
                            if '.' not in url or len(extension)>7:
                                extension = None
                            page.site_id = site.id
                            page.url = url    #url страницы
                            page.image_type = extension    #разрешение картинки
                            page.image_page = page_obj    #Страница связанная модель
                            page.image_item = item
                            page.image_counter = start_num_count
                            page.status = ChoicesStatus.PICTURE_NOT_EXTRACTED    #картинка не извлекалась
                            page.type_page = ChoicesPage.IMG    #тип страницы картинка
                            page.save()
                            start_num_count+=1
                    page_obj.status = ChoicesStatus.SUCCESSFULLY_IMAGE_URL
                    # page_obj.attempts = 0
                    page_obj.html_page = ''    #очищаем html
                    page_obj.save()
                    return Response(status=HTTP_201_CREATED)

        except NonVendorCode:
            return Response(f'{page_pk} нет артикула', status=HTTP_201_CREATED)

        except ObjectDoesNotExist as e:    #если нету snippet по pk в бд
            return Response(f'Элемент с id-{page_pk} не найден в бд', status=HTTP_500_INTERNAL_SERVER_ERROR)

        except TransactionManagementError as e:    # поднимается для любых и всех проблем, связанных с транзакциями базы данных.
            return Response(f'{str(e)} ошибка транзакции {page.pk}', status=HTTP_500_INTERNAL_SERVER_ERROR)

        except DatabaseError as e:    #ловим ошибки бд
            page_obj = Page.objects.get(pk=page_pk)
            page_obj.status = ChoicesStatus.SUCCESSFULLY_ITEM
            page_obj.save()
            return Response(f'{str(e)} Ошибка в бд', status=HTTP_500_INTERNAL_SERVER_ERROR)

        except FieldError as e:    #Исключение FieldError вызывается, если существует проблема с полем модели.
            return Response(f'{str(e)} ошибка в запрашиваемых полях {page_pk}', status=HTTP_500_INTERNAL_SERVER_ERROR)

        except ValidationError as e:
            page = Page.objects.get(pk=page_pk)
            page.status = ChoicesStatus.ERROR_GET_IMAGE  # "Ошибка валидации post запроса с url"
            page.save()
            return Response('Произошла проблема с валидацией', status=HTTP_500_INTERNAL_SERVER_ERROR)

        except Error as e:    #Основная для ошибок связанных с бд
            return Response(f'Ошибка в бд {str(e)}', status=HTTP_500_INTERNAL_SERVER_ERROR)

        except ConnectionError  as e:
            return Response(str(e), status=HTTP_500_INTERNAL_SERVER_ERROR)

        except Exception as e:
            page_obj = Page.objects.get(pk=page_pk)
            page_obj.status = ChoicesStatus.SUCCESSFULLY_ITEM
            page_obj.save()
            return Response(str(e), status=HTTP_500_INTERNAL_SERVER_ERROR)

#________________________________________________________________

    def extract_base64(self, request: HttpRequest,  cnt: int, *args, **kwargs):
        """ для получение url картинок
            loader/next-image-url/<int:cnt>/"""
        try:
            with transaction.atomic():
                # records = Page.objects.filter(type_page=ChoicesPage.IMG, status=ChoicesStatus.PICTURE_NOT_EXTRACTED).order_by('-time_update')[:cnt]  # продукт со статусом <Страница обработана, товар извлечён, готова к извлечению картинок
                records = Page.objects.raw("""SELECT uap.id, uap.time_create, uap.time_update, uap.url
                                            FROM urlopen_app_page as uap
                                            WHERE uap.status = %s and uap.type_page = %s
                                            ORDER BY uap.time_update desc
                                            LIMIT %s""", [ChoicesStatus.PICTURE_NOT_EXTRACTED, ChoicesPage.IMG, cnt])
                self.change_status(records, ChoicesStatus.THE_PROCESS_IMAGE_EXTRACTION)    #THE_PROCESS_IMAGE_EXTRACTION
                serializer = LoaderNextSerializer(records, many=True)
                return Response(serializer.data, status=HTTP_201_CREATED)

        except TransactionManagementError as e:    # поднимается для любых и всех проблем, связанных с транзакциями базы данных.
            return Response(f'{str(e)} ошибка транзакции {records}', status=HTTP_500_INTERNAL_SERVER_ERROR)

        except OperationalError as e:    #Операционная ошибка
            return Response(f'{str(e)} ошибка сохранения в базу {records}', status=HTTP_500_INTERNAL_SERVER_ERROR)

        except DatabaseError as e:    #ловим ошибки бд
            return Response(f'{str(e)} Ошибка в бд', status=HTTP_500_INTERNAL_SERVER_ERROR)

        except FieldError as e:
            return Response(f'{str(e)} ошибка в запрашиваемых полях {records}', status=HTTP_500_INTERNAL_SERVER_ERROR)

        except Error as e:    #общая для баз данных
            return Response(f'{str(e)} ошибка бд {records}', status=HTTP_500_INTERNAL_SERVER_ERROR)

        except Exception as e:
            return Response(str(e), status=HTTP_500_INTERNAL_SERVER_ERROR)


    def put_base64(self, request: HttpRequest, site_pk: int, page_pk: int, *args, **kwargs):
        """ для добавления base64 картинки
            putbase64/<int:site_pk>/<int:page_pk>"""

        try:
            snippet = Page.objects.get(pk=page_pk)
            serializer = GetHtmlSerialiser(snippet, data=request.data)
            with transaction.atomic():
                if serializer.is_valid(raise_exception=True):
                    serializer.save()
                    return Response(status=HTTP_201_CREATED)

        except ObjectDoesNotExist as e:    #если нету snippet по pk в бд
            return Response(f'Элемент с id-{page_pk} не найден в бд', status=HTTP_500_INTERNAL_SERVER_ERROR)

        except TransactionManagementError as e:    # поднимается для любых и всех проблем, связанных с транзакциями базы данных.
            return Response(f'{str(e)} ошибка транзакции {snippet.pk}', status=HTTP_500_INTERNAL_SERVER_ERROR)

        except OperationalError as e:    #Операционная ошибка
            return Response(f'{str(e)} ошибка сохранения в базу {snippet}', status=HTTP_500_INTERNAL_SERVER_ERROR)

        except DatabaseError as e:    #ловим ошибки бд
            snippet = Page.objects.get(pk=page_pk)
            snippet.status = ChoicesStatus.PICTURE_NOT_EXTRACTED
            snippet.save()
            return Response(f'{str(e)} Ошибка в бд', status=HTTP_500_INTERNAL_SERVER_ERROR)

        except FieldError as e:    #Исключение FieldError вызывается, если существует проблема с полем модели.
            return Response(f'{str(e)} ошибка в запрашиваемых полях {page_pk}', status=HTTP_500_INTERNAL_SERVER_ERROR)

        except ValidationError as e:
            snippet = Page.objects.get(pk=page_pk)
            snippet.status = ChoicesStatus.ERROR_GET_IMAGE
            snippet.save()
            return Response(f'Ошибка валидации, объекта {snippet.pk}', status=HTTP_500_INTERNAL_SERVER_ERROR)

        except Error as e:    #Основная для ошибок связанных с бд
            snippet = Page.objects.get(pk=page_pk)
            snippet.status = ChoicesStatus.HTML_SUCCESSFULLY
            snippet.save()
            return Response(f'Ошибка в бд {str(e)}', status=HTTP_500_INTERNAL_SERVER_ERROR)

        except ConnectionError  as e:    #Базовый класс для проблем, связанных с подключением.
            return Response(f'{str(e)} Проблемы с подключением', status=HTTP_500_INTERNAL_SERVER_ERROR)

        except Exception as e:
            return Response(str(e), status=HTTP_500_INTERNAL_SERVER_ERROR)

#________________________________________________________________

    # def decode_image(self, request:HttpRequest, cnt: int, *args, **kwargs):
    #     """ получение html картинки для дальнейшего декодирования и сохранения """
    #     try:
    #         with transaction.atomic():
    #             # records = Page.objects.raw("""select uap.id, uap.html_page, uap.image_type, uap.image_counter, uap.time_create,
	#             #                                     uap.time_update, uas.domain_name, uap.site_id, uai.brand, uai.vendor_code, uap.image_item_id, uas.pattern_path
    #             #                               from urlopen_app_page uap
    #             #                               left join urlopen_app_site uas
    #             #                               on uas.id = uap.site_id
    #             #                               left join urlopen_app_item uai
    #             #                               on uai.id = uap.image_item_id
    #             #                               where uap.type_page = %s and uap.status = %s
    #             #                               order by uap.time_update desc
    #             #                               limit %s""", [ChoicesPage.IMG, ChoicesStatus.SUCCESSFULLY_IMAGE, cnt])    #получение недекодированной картинки
    #             records = Page.objects.raw("""select uap.id, uap.html_page, uap.image_type, uap.image_counter, uap.time_create,
	#                                             uap.time_update, uas.domain_name, uap.site_id, uai.brand, uai.vendor_code, uap.image_item_id, uas.pattern_path
    #                                             from urlopen_app_page uap
    #                                             left join urlopen_app_item uai
    #                                             on uai.id = uap.image_item_id
    #                                             left join urlopen_app_site uas
    #                                             on uas.id = uap.site_id
    #                                             where uap.type_page = %s and uap.status = %s
    #                                             order by uap.time_update desc
    #                                             limit %s""", [ChoicesPage.IMG, ChoicesStatus.SUCCESSFULLY_IMAGE, cnt])    #получение недекодированной картинки
    #             self.change_status(records, ChoicesStatus.IN_PROCESS_DECODE)    #IN_PROCESS_DECODE изменение статуса на в впроцессе декодирования
    #             serializer = ImageDecodeSerializer(records, many=True)
    #             return Response(serializer.data, status=HTTP_201_CREATED)

    #     except TransactionManagementError as e:    # поднимается для любых и всех проблем, связанных с транзакциями базы данных.
    #         return Response(f'{str(e)} ошибка транзакции {records}', status=HTTP_500_INTERNAL_SERVER_ERROR)

    #     except OperationalError as e:    #Операционная ошибка
    #         return Response(f'{str(e)} ошибка сохранения в базу {records}', status=HTTP_500_INTERNAL_SERVER_ERROR)

    #     except DatabaseError as e:    #ловим ошибки бд
    #         return Response(f'{str(e)} Ошибка в бд', status=HTTP_500_INTERNAL_SERVER_ERROR)

    #     except FieldError as e:
    #         return Response(f'{str(e)} ошибка в запрашиваемых полях {records}', status=HTTP_500_INTERNAL_SERVER_ERROR)

    #     except Error as e:    #общая для баз данных
    #         return Response(f'{str(e)} ошибка бд {records}', status=HTTP_500_INTERNAL_SERVER_ERROR)

    #     except Exception as e:
    #         return Response(str(e), status=HTTP_500_INTERNAL_SERVER_ERROR)


    # def post_image(self, request: HttpRequest, page_pk: int, *args, **kwargs):
    #     """ изменение статуса у картинки после её декодирования"""
    #     try:
    #         snippet = Page.objects.get(pk=page_pk)    #получение id страницы
    #         serializer = DecodeSerializer(data=request.data)
    #         if serializer.is_valid(raise_exception=True):
    #             with transaction.atomic():
    #                 data = serializer.validated_data
    #                 image_path = data.get('image_path', '')    #извлечение image_path из валидных данных
    #                 snippet.status = data.get('status', ChoicesStatus.SUCCESSFULLY_IMAGE)     #изменение статуса
    #                 if snippet.status==ChoicesStatus.SUCCESSFULLY_DECODE_IMG:
    #                     snippet.image_path = image_path
    #                     # snippet.html_page = ''     #добавить если мне не нужно будет хранить base64
    #                 snippet.save()
    #                 return Response(status = HTTP_201_CREATED)

    #     except ObjectDoesNotExist as e:    #если нету snippet по pk в бд
    #         return Response(f'Элемент с id-{page_pk} не найден в бд', status=HTTP_500_INTERNAL_SERVER_ERROR)

    #     except TransactionManagementError as e:    # поднимается для любых и всех проблем, связанных с транзакциями базы данных.
    #         return Response(f'{str(e)} ошибка транзакции {snippet.pk}', status=HTTP_500_INTERNAL_SERVER_ERROR)

    #     except OperationalError as e:    #Операционная ошибка
    #         return Response(f'{str(e)} ошибка сохранения в базу {snippet}', status=HTTP_500_INTERNAL_SERVER_ERROR)

    #     except DatabaseError as e:    #ловим ошибки бд
    #         snippet = Page.objects.get(pk=page_pk)
    #         snippet.status = ChoicesStatus.SUCCESSFULLY_IMAGE
    #         snippet.save()
    #         return Response(f'{str(e)} Ошибка в бд', status=HTTP_500_INTERNAL_SERVER_ERROR)

    #     except FieldError as e:    #Исключение FieldError вызывается, если существует проблема с полем модели.
    #         return Response(f'{str(e)} ошибка в запрашиваемых полях {page_pk}', status=HTTP_500_INTERNAL_SERVER_ERROR)

    #     except ValidationError as e:
    #         snippet = Page.objects.get(pk=page_pk)
    #         snippet.status = ChoicesStatus.ERROR_DECODE_IMAGE
    #         snippet.save()
    #         return Response(f'Ошибка валидации, объекта {snippet.pk}', status=HTTP_500_INTERNAL_SERVER_ERROR)

    #     except Error as e:    #Основная для ошибок связанных с бд
    #         snippet = Page.objects.get(pk=page_pk)
    #         snippet.status = ChoicesStatus.ERROR_DECODE_IMAGE
    #         snippet.save()
    #         return Response(f'Ошибка в бд {str(e)}', status=HTTP_500_INTERNAL_SERVER_ERROR)

    #     except ConnectionError  as e:    #Базовый класс для проблем, связанных с подключением.
    #         return Response(f'{str(e)} Проблемы с подключением', status=HTTP_500_INTERNAL_SERVER_ERROR)

    #     except Exception as e:
    #         return Response(str(e), status=HTTP_500_INTERNAL_SERVER_ERROR)


#________________________________________________________________

    def attempt_error(self, request:HttpRequest, page_pk: int, *args, **kwargs):
        """ специальный метод для добавления attempt и сохранения другого статуса
            change-status/<int:page_pk>/
        """
        try:
            snippet = Page.objects.get(pk=page_pk)    #получение id
            site =snippet.site    #получение site
            site_attempt = site.attempts    #получение с сайте колличество attempt
            serializer = AttemptSerializer(data=request.data)
            if serializer.is_valid(raise_exception=True):
                with transaction.atomic():
                    data = serializer.validated_data
                    if snippet.attempts<site_attempt:
                        snippet.attempts += 1
                        snippet.status = data.get('status',ChoicesStatus.NOT_PROCESSED_HTML)
                        snippet.save()
                    else:
                        snippet.status = ChoicesStatus.ERROR_ATTEMPT_FABRIC
                        snippet.attempts = 0
                        snippet.save()
                    return Response(status = HTTP_201_CREATED)

        except ObjectDoesNotExist as e:    #если нету snippet по pk в бд
            return Response(f'Элемент с id-{page_pk} не найден в бд', status=HTTP_500_INTERNAL_SERVER_ERROR)

        except TransactionManagementError as e:    # поднимается для любых и всех проблем, связанных с транзакциями базы данных.
            return Response(f'{str(e)} ошибка транзакции {snippet.pk}', status=HTTP_500_INTERNAL_SERVER_ERROR)

        except DatabaseError as e:    #ловим ошибки бд
            return Response(f'{str(e)} Ошибка в бд на get запросе', status=HTTP_500_INTERNAL_SERVER_ERROR)

        except FieldError as e:    #Исключение FieldError вызывается, если существует проблема с полем модели.
            return Response(f'{str(e)} ошибка в запрашиваемых полях {snippet.pk}', status=HTTP_500_INTERNAL_SERVER_ERROR)

        except ValidationError as e:
            snippet = Page.objects.get(pk=page_pk)
            snippet.status = ChoicesStatus.ERROR_ATTEMPT  # "Ошибка валидации в attempt_error"
            snippet.save()
            return Response('Произошла проблема с валидацией сериалайзера', status=HTTP_500_INTERNAL_SERVER_ERROR)

        except Error as e:    #Основная для ошибок связанных с бд
            return Response(f'Ошибка в бд {str(e)}', status=HTTP_500_INTERNAL_SERVER_ERROR)

        except ConnectionError  as e:
            return Response(str(e), status=HTTP_500_INTERNAL_SERVER_ERROR)

        except Exception as e:
            return Response('Ошибка при изменении attempta', status=HTTP_500_INTERNAL_SERVER_ERROR)


class LoginAPIView(APIView):
    """ авторизация  """
    permission_classes = (AllowAny,)
    renderer_classes = (UserJSONRenderer,)
    serializer_class = LoginSerializer

    def post(self, request: HttpRequest) -> Response:
        user = {}
        if 'user' in request.data:
            user = request.data.get('user')

        if not user and 'password' in request.data and 'username' in request.data:
            user['username'] = request.data.get('username')
            user['password'] = request.data.get('password')

        serializer = self.serializer_class(data=user)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data, status=status.HTTP_200_OK)