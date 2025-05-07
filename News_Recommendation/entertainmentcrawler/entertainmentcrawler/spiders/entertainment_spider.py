import scrapy
from ..items import EntertainmentcrawlerItem
from news.models import ENHeadline
from entertainmentcrawler.spiders import entertainment_spider
from entertainmentcrawler import pipelines

class EntertainmentSpider(scrapy.Spider):
    name = "entertainment"
    start_urls = [
        'https://indianexpress.com/videos/'
    ]

    def parse(self, response):
        div_all_news = response.xpath("//div[@class='nation']//div[@class='articles']")

        for article in div_all_news:
            title = article.xpath(".//h2/a/text()").get()
            link = article.xpath(".//div[@class='snaps']/a/@href").get()

            # Extract image from <noscript>
            img_tag = article.xpath(".//div[@class='snaps']/a/noscript").get()
            img = scrapy.Selector(text=img_tag).xpath("//img/@src").get() if img_tag else None
            
            # Handle relative URLs
            if link and not link.startswith('http'):
                link = f'https://indianexpress.com{link}'
            if img and not img.startswith('http'):
                img = f'https://indianexpress.com{img}'

            if title and link:
                yield scrapy.Request(
                    url=link,
                    callback=self.parse_article,
                    meta={'title': title, 'link': link, 'img': img}
                )

    def parse_article(self, response):
        items = EntertainmentcrawlerItem()

        title = response.meta.get('title')
        link = response.meta.get('link')
        img = response.meta.get('img')

        # Extract article content
        content = response.xpath("//div[@class='full-details']//p//text()").getall()
        news_content = ' '.join(content).strip()

        truncated_content = ' '.join(news_content.split()[:200])

        if title and link:
            items["title"] = title
            items["image"] = img 
            items["content"] = truncated_content or 'No content available.'
            items["url"] = link
            items['source'] = 'Indian Express'

            yield items

        
class EntrtnmentSpider(scrapy.Spider):
    name = "entrtnment"
    start_urls = [
        'https://www.foxnews.com/entertainment'
    ]

    def parse(self, response):
        div_all_news = response.xpath("//div[@class='content article-list']/article")

        for article in div_all_news:
            title = article.xpath(".//div[@class='info']/header/h4/a/text()").get()
            link = article.xpath(".//div[@class='m']/a/@href").get()
            img = article.xpath(".//div[@class='m']/a/img/@src").get()

            # Handle relative URLs
            if link and not link.startswith('http'):
                link = f'https://www.foxnews.com{link}'
            if img and not img.startswith('http'):
                img = f'https://www.foxnews.com{img}'

            if title and link:
                yield scrapy.Request(
                    url=link,
                    callback=self.parse_article,
                    meta={'title': title, 'link': link, 'img': img}
                )

    def parse_article(self, response):
        items = EntertainmentcrawlerItem()

        title = response.meta.get('title')
        link = response.meta.get('link')
        img = response.meta.get('img')
        
        # Extract article content
        content = response.xpath("//div[@class='article-body']//p//text()").getall()
        news_content = ' '.join(content).strip()

        truncated_content = ' '.join(news_content.split()[:100])

        if title and link:
            items["title"] = title
            items["image"] = img or 'https://example.com/default.jpg'
            items["content"] = truncated_content or 'No content available.'
            items["url"] = link
            items['source'] = 'Fox News'

            yield items