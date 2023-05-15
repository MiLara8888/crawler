#!/usr/bin/env python
# -- coding: utf-8 --
"""
хранение и распространение choices
"""
from django.db import models


class ChoicesStatus(models.IntegerChoices):
    '''
    Для определения статуса получения html страницы
    '''
    SUCCESSFULLY_ITEM = 0, 'Страница обработана, товар извлечён, готова к извлечению url-ok картинок товара'
    IN_PROCESS_IMAGE = 1, 'Страница обработана и в процессе извлечения url картинок'
    SUCCESSFULLY_IMAGE_URL = 2, 'URL картинок и товары успешно извлечены'


    #для страниц-картинок
    PICTURE_NOT_EXTRACTED = 3, 'Картинка не извлекалась'
    THE_PROCESS_IMAGE_EXTRACTION = 4, 'В процессе извлечения картинки'
    SUCCESSFULLY_IMAGE = 5, 'Картинка готова к декодированию'
    IN_PROCESS_DECODE = 6, 'Картинка в процессе декодирования'
    SUCCESSFULLY_DECODE_IMG = 7, 'Картинка успешно извлечена в папку'

    SUCCESSFULLY_ITEM_NOT_VENDOR_CODE = 8, 'Страница обработана, товар извлечён, артикула в модели товары нет'


    NOT_PROCESSED_HTML = 20, 'Html станицы не извлекался'
    IN_PROCESS_HTML = 21, 'В процессе извлечения html'

    HTML_SUCCESSFULLY = 30, 'HTML успешно извлечён страница готова к извлечению url-ок'
    IN_PROCESS_PARS = 31, 'Страница в процессе извлечения url'
    SUCCESSFULLY_URL = 32, 'Из страницы успешно извлечены url страница готова к определению типа'

    IN_PROCESS_TYPE = 51, 'Страница в процессе определения типа'
    SUCCESSFULLY_TYPE = 52, 'Тип страницы успешно определён, страница готова к отправке на фабрику'

    FACTORY_VISIT = 60, 'Страница отправлена на фабрику и в процессе извлечения информации'

    ERROR = 90, 'Ошибка получения html страницы'
    ERROR_VALIID_HTML = 91, "Ошибка при валидации html"

    ERROR_VALIID_PARSE = 92, "Ошибка при валидации данных из парсера"
    PAGE_WITHOUT_URL = 93, "Страница не содержит url"
    ERROR_FACTORY_VALID = 94, "Ошибка валидации фабрики"
    ERROR_PARSE_URL = 95, "Ошибка при извлечении url со страницы"
    ERROR_URL_PARSE = 96, "Ошибка валидации post запроса с url"
    ERROR_VALID_TYPE = 97, "Ошибка при валидации данных при определении типа сраницы"
    ERROR_GET_DATA = 98, "Ошибка валидации внутри loader, какие-то данные переданы не корректно"
    ERROR_UNIQUE = 99, "Ошибка сохранения товара со страницы, этот объект уже присутствует в базе"
    ERROR_ATTEMPT_FABRIC = 100, "Не удалось извлечь данные о товаре за заданное колличество попыток"
    EROR_ATTEMPT = 101, "Ошибка валидации в attempt_error"
    ERROR_PAGE_TYPE = 102, "Ошибка валидации словаря с типами страницы"
    ERROR_VALID_IMAGE = 103, "Ошибка валидации и сохранения изображения"
    ERROR_GET_IMAGE = 104, "Ошибка извлечения картинки"
    ERROR_DECODE_IMAGE = 105, "Ошибка декодирования картинки"


    # ERROR = 40, 'Ошибка получения html страницы'
    # ERROR_VALIID_HTML = 41, "Ошибка при валидации html"
    # ERROR_VALIID_PARSE = 42, "Ошибка при валидации данных из парсера"
    # PAGE_WITHOUT_URL = 43, "Страница не содержит url"
    # ERROR_FACTORY_VALID = 44, "Ошибка валидации фабрики"
    # ERROR_PARSE_URL = 45, "Ошибка при извлечении url со страницы"
    # ERROR_URL_PARSE = 46, "Ошибка валидации post запроса с url"
    # ERROR_VALID_TYPE = 47, "Ошибка при валидации данных при определении типа сраницы"
    # ERROR_GET_DATA = 48, "Ошибка валидации внутри loader, какие-то данные переданы не корректно"
    # ERROR_UNIQUE = 49, "Ошибка сохранения товара со страницы, этот объект уже присутствует в базе"
    # ERROR_ATTEMPT_FABRIC = 401, "Не удалось извлечь данные о товаре за заданное колличество попыток"



class ChoicesPage(models.IntegerChoices):
    '''
    Для определения типа страницы
    '''
    NONE = 0, 'Пока неопределён'
    BRAND = 10, 'Страница бренда'
    ITEM = 20, 'Продукт'
    KOLLECT = 30, 'Коллекция'
    BASE = 40, 'Основная страница'
    NONE_TYPE = 50, 'Без типа'
    IMG = 60, 'Картинка'
    IMG_BRAND = 70, 'Картинка бренда'