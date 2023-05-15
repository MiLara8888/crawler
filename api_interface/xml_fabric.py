#!/usr/bin/env python
# -- coding: utf-8 --
"""
"""
import xml.etree.ElementTree as ET
from io import BytesIO
from urlopen_app.models import Item


class XmlRendererSite:
    """преобразователь в xml для модели сайта"""
    def __init__(self, raw_data = None):
        self.raw_data = raw_data   #данные из бд
        self.result = ET.Element('root')

    def formation_xml(self):
        for i in self.raw_data:
            domain_name = ET.Element('domain_name', name=str(i.domain_name))
            if 'id' in i.__dict__:
                elem = ET.Element('id')
                elem.text = str(i.id)
                domain_name.append(elem)
            if 'url' in i.__dict__:
                elem = ET.Element('url')
                elem.text = str(i.url)
                domain_name.append(elem)
            if 'time_create' in i.__dict__:
                elem = ET.Element('time_create')
                elem.text = str(i.time_create)
                domain_name.append(elem)
            # if 'time_update' in i.__dict__:
            #     elem = ET.Element('time_update')
            #     elem.text = str(i.time_update)
            #     domain_name.append(elem)
            # if 'json_data' in i.__dict__:
            #     elem = ET.Element('json_data')
            #     elem.text = str(i.json_data)
            #     domain_name.append(elem)
            # if 'attempts' in i.__dict__:
                # elem = ET.Element('attempts')
                # elem.text = str(i.attempts)
                # domain_name.append(elem)
            self.result.append(domain_name)
            xml_str = ET.tostring(self.result, encoding="utf-8", method="xml")
            n = ET.ElementTree(self.result)
            f = BytesIO()
            n.write(f, encoding='utf-8', xml_declaration=True)
        return f



# site time_create time_update json_data attempts page name unit wholesale_price sales_price vendor_code site_code brand


class XmlRendererError:
    def __init__(self, raw_data = None, count = None):
        self.raw_data = raw_data
        self.result = ET.Element('data')


    def formation_xml(self):
            obj = ET.Element('error')
            obj.text = str(self.raw_data['error'])
            self.result.append(obj)
            xml_str = ET.tostring(self.result, encoding="utf-8", method="xml")
            n = ET.ElementTree(self.result)
            f = BytesIO()
            n.write(f, encoding='utf-8', xml_declaration=True)
            return f


# class XmlRendererToken:
#     def __init__(self, raw_data = None, count = None):
#         self.raw_data :dict = raw_data
#         self.result = ET.Element('data')


#     def formation_xml(self):
#             obj = ET.Element('error')
#             obj.text = str(self.raw_data['error'])
#             self.result.append(obj)
#             xml_str = ET.tostring(self.result, encoding="utf-8", method="xml")
#             n = ET.ElementTree(self.result)
#             f = BytesIO()
#             n.write(f, encoding='utf-8', xml_declaration=True)
#             return f


class XmlRendererItem:
    """преобразователь в xml для модели Item"""
    def __init__(self, raw_data = None):
        self.raw_data = raw_data   #данные из бд
        self.result = ET.Element('data')
        self._add_count()

    def _add_count(self):
        item_count = Item.objects.all().count()
        count_tag = ET.Element('count')
        count_tag.text = str(item_count)
        self.result.append(count_tag)

    def formation_xml(self):
        items_tag = ET.Element('items')
        for i in self.raw_data:
            item = ET.Element('item')
            # items_tag.append(item)
            if 'id' in i.__dict__:
                elem = ET.Element('id')
                # elem = ET.Element('id', type="xs:integer")    #TODO явное указание типов
                elem.text = str(i.id)
                item.append(elem)
            if 'name' in i.__dict__:
                elem = ET.Element('name')
                elem.text = str(i.name)
                item.append(elem)
            if 'site' in i.__dict__:
                elem = ET.Element('site')
                elem.text = str(i.site)
                item.append(elem)
            # if 'json_data' in i.__dict__:
            #     elem = ET.Element('json_data')
            #     elem.text = str(i.json_data)
            #     item.append(elem)
            if 'json_data' in i.__dict__:
                elem = ET.Element('characteristics')
                if 'characteristics' in i.json_data:
                    for k,m in i.json_data['characteristics'].items():
                        obj = ET.Element('subject', name=k)
                        obj.text = m
                        elem.append(obj)
                item.append(elem)
            if 'time_create' in i.__dict__:
                elem = ET.Element('time_create')
                cre_date = (i.time_create).strftime("%d.%m.%Y")
                elem.text = str(cre_date)
                item.append(elem)
            if 'time_update' in i.__dict__:
                elem = ET.Element('time_update')
                up_date = (i.time_update).strftime("%d.%m.%Y")
                elem.text = str(up_date)
                item.append(elem)
            if 'page' in i.__dict__:
                elem = ET.Element('page')
                elem.text = str(i.page)
                item.append(elem)
            if 'sales_price' in i.__dict__:
                elem = ET.Element('price')
                number = format(float(i.sales_price), '.2f')
                elem.text = str(number)
                item.append(elem)
            if 'wholesale_price' in i.__dict__:
                elem = ET.Element('wholesale_price')
                elem.text = str(i.wholesale_price)
                item.append(elem)
            if 'unit' in i.__dict__:
                elem = ET.Element('unit')
                elem.text = str(i.unit)
                item.append(elem)
            if 'vendor_code' in i.__dict__:
                elem = ET.Element('article')
                elem.text = str(i.vendor_code)
                item.append(elem)
            if 'site_code' in i.__dict__:
                elem = ET.Element('site_code')
                elem.text = str(i.site_code)
                item.append(elem)
            if 'brand' in i.__dict__:
                elem = ET.Element('brand')
                elem.text = str(i.brand)
                item.append(elem)
            items_tag.append(item)
            # self.result.append(items_tag)
        self.result.append(items_tag)
        xml_str = ET.tostring(self.result, encoding="utf-8", method="xml")
        n = ET.ElementTree(self.result)
        f = BytesIO()
        n.write(f, encoding='utf-8', xml_declaration=True)
        return f


    # def formation_xml(self):
    #     items_tag = ET.Element('Items')
    #     for i in self.raw_data:
    #         item = ET.Element('Item')
    #         # items_tag.append(item)
    #         if 'id' in i.__dict__:
    #             elem = ET.Element('Id')
    #             # elem = ET.Element('id', type="xs:integer")    #TODO явное указание типов
    #             elem.text = str(i.id)
    #             item.append(elem)
    #         if 'name' in i.__dict__:
    #             elem = ET.Element('Name')
    #             elem.text = str(i.name)
    #             item.append(elem)
    #         if 'site' in i.__dict__:
    #             elem = ET.Element('Site')
    #             elem.text = str(i.site)
    #             item.append(elem)
    #         # if 'json_data' in i.__dict__:
    #         #     elem = ET.Element('json_data')
    #         #     elem.text = str(i.json_data)
    #         #     item.append(elem)
    #         if 'json_data' in i.__dict__:
    #             elem = ET.Element('Characteristics')
    #             if 'characteristics' in i.json_data:
    #                 for k,m in i.json_data['characteristics'].items():
    #                     obj = ET.Element('subject', name=k)
    #                     obj.text = m
    #                     elem.append(obj)
    #             item.append(elem)
    #         if 'time_create' in i.__dict__:
    #             elem = ET.Element('Time_create')
    #             cre_date = (i.time_create).strftime("%d.%m.%Y")
    #             elem.text = str(cre_date)
    #             item.append(elem)
    #         if 'time_update' in i.__dict__:
    #             elem = ET.Element('Time_update')
    #             up_date = (i.time_update).strftime("%d.%m.%Y")
    #             elem.text = str(up_date)
    #             item.append(elem)
    #         if 'page' in i.__dict__:
    #             elem = ET.Element('Page')
    #             elem.text = str(i.page)
    #             item.append(elem)
    #         if 'sales_price' in i.__dict__:
    #             elem = ET.Element('Sales_price')
    #             number = format(float(i.sales_price), '.2f')
    #             elem.text = str(number)
    #             item.append(elem)
    #         if 'wholesale_price' in i.__dict__:
    #             elem = ET.Element('Wholesale_price')
    #             elem.text = str(i.wholesale_price)
    #             item.append(elem)
    #         if 'unit' in i.__dict__:
    #             elem = ET.Element('Unit')
    #             elem.text = str(i.unit)
    #             item.append(elem)
    #         if 'vendor_code' in i.__dict__:
    #             elem = ET.Element('Vendor_code')
    #             elem.text = str(i.vendor_code)
    #             item.append(elem)
    #         if 'site_code' in i.__dict__:
    #             elem = ET.Element('Site_code')
    #             elem.text = str(i.site_code)
    #             item.append(elem)
    #         if 'brand' in i.__dict__:
    #             elem = ET.Element('Brand')
    #             elem.text = str(i.brand)
    #             item.append(elem)
    #         self.result.append(item)
    #         # self.result.append(items_tag)
    #         xml_str = ET.tostring(self.result, encoding="utf-8", method="xml")
    #         n = ET.ElementTree(self.result)
    #         f = BytesIO()
    #         n.write(f, encoding='utf-8', xml_declaration=True)
    #     return f




# root = ET.Element('data')    #коренб дерева
# country = ET.Element('country', name="Liechtenstein")
# rank = ET.Element('rank', updated="yes")
# rank.text = '2'
# country.append(rank)
# year = ET.Element('year')
# year.text = '2008'
# country.append(year)
# gdppc = ET.Element('gdppc')
# gdppc.text = '141100'
# country.append(gdppc)
# country.append(ET.Element('neighbor', name="Austria", direction="E"))
# country.append(ET.Element('neighbor', name="Switzerland", direction="W"))
# root.append(country)
# country = ET.Element('country', name="Singapore")
# root.append(country)
# # NOTE: По аналогии выше сами заполните нужные вам страны
# xml_str = ET.tostring(root, encoding="utf-8", method="xml")
# print(xml_str.decode(encoding="utf-8"))
# <data>
#   <country name="Liechtenstein">
#     <rank updated="yes">2</rank>
#     <year>2008</year>
#     <gdppc>141100</gdppc>
#     <neighbor direction="E" name="Austria" />
#     <neighbor direction="W" name="Switzerland" />
#   </country>
#   <country name="Singapore" />
# </data>

