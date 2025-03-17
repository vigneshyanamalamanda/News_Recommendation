import scrapy
from scrapy_djangoitem import DjangoItem

import sys

import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'News_Aggregator.settings'

from news.models import Headline

class NewscrawlerItem(DjangoItem):
    # define the fields for your item here like:
    name = scrapy.Field()
    django_model = Headline
    content = scrapy.Field()  # Add this field
