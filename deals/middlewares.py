from datetime import datetime
from lib.file_storage import write_file, write_gzip


class HtmlStorageMiddleware(object):
    """
    Scrapy Downloader middleware to store request responses to local disk
    """
    def __init__(self, settings):
        """
        Args:
            settings (scrapy.settings.Settings)
        """
        self.settings = settings.get('HTML_STORAGE', {})
        self.compress = self.settings.get('COMPRESS', False)
        self.path = self.settings.get('PATH', '~/storage/')

    @classmethod
    def from_settings(self, settings):
        """Contruct middleware with scrapy settings.
        Args:
            settings (scrapy.settings.Settings)
        Returns:
            HtmlStorageMiddleware:
        """
        return HtmlStorageMiddleware(settings)

    def process_response(self, request, response, spider):
        """Stores response HTML body to file.
        Args:
            request (scrapy.http.request.Request): request which triggered
                this response.
            response (scrapy.http.Response)
            spider: (scrapy.Spider): spider that triggered the request.
                Spiders must set 'started_crawling' field to Unix timestamp.
        Returns:
            scrapy.http.response.Response: unmodified response object.
        """
        if not spider.replay:
            self.save_response(spider.name, response.body)

        return response

    def save_response(self, spider_name, html_body):
        """Store html to file.
        Optionally file will be gzipped.
        Args:
            str(spider_name): file path to save html to.
            str(html_body): file content.
        """

        dt = datetime.now()
        filename = "{}-{}".format(
            spider_name, dt.strftime("%H:%M:%S:%f"))
        file_path = "{}/{}/{}/{}.html".format(
            self.path,
            spider_name,
            dt.date(),
            filename
        )
        func = write_file

        if self.compress:
            func = write_gzip

        func(file_path, html_body)
