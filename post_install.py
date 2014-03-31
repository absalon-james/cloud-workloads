import os
import urllib2
from setuptools.command.install import install
from setuptools.command.develop import develop


class PostInstallDownloader(object):

    CHUNK_SIZE = 64 * 1024

    def prep_dir(self, download_dict):
        """
        Makes sures that parent directories of the dst location
        exist.

        @param download_dict - Download dictionary describing download

        """
        dirname, filename = os.path.split(download_dict['dst'])
        if not os.path.exists(dirname):
            os.makedirs(dirname)

    def download_header(self, download_dict):
        """
        Shows a header line before executing a download.

        @param download_dict - Download dictionary describing download

        """
        print "\nDownloading %s" % download_dict['src']

    def download_footer(self, download_dict):
        """
        Shows a footer after every download.

        @param download_dict - Download dictionary describing download

        """
        print "Saved to %s" % download_dict['dst']

    def download_many(self, download_list):
        """
        Downloads multiple files synchronously.

        @param download_list - List of dictionaries describing downloads

        """
        for download_dict in download_list:
            self.download(download_dict)

    def download(self, download_dict):
        """
        Downloads a file according to download_dict.
        download_dict should have keys for 'src' and 'dst'
        'src' should be a url indicating location of file to download
        'dst' should be a path indicating where on the file system to
            place the downloaded file.

        @param download_dict - Dictionary describing download.

        """
        self.prep_dir(download_dict)
        self.download_header(download_dict)
        req = urllib2.urlopen(download_dict['src'])
        so_far = 0
        with open(download_dict['dst'], 'w') as f:
            write = lambda: req.read(self.CHUNK_SIZE)
            for chunk in iter(write, ''):
                so_far += len(chunk)
                f.write(chunk)
        self.download_footer(download_dict)


# TODO - Maybe move this to json and load it in
post_install_download_files = [
    {
        'src': 'http://91130b1325445faefa46-0a57a58cc8418ee081f89836dd343dea.r74.cf1.rackcdn.com/drupal.db.tar.gz',
        'dst': '/srv/salt/drupal/files/drupal.db.tar.gz'
    },
    {
        'src': 'http://91130b1325445faefa46-0a57a58cc8418ee081f89836dd343dea.r74.cf1.rackcdn.com/drupal_web.tar.gz',
        'dst': '/srv/salt/drupal/files/drupal_web.tar.gz'
    },
    {
        'src': 'http://91130b1325445faefa46-0a57a58cc8418ee081f89836dd343dea.r74.cf1.rackcdn.com/magento-sample-data.sql',
        'dst': '/srv/salt/magento/files/sample-data.sql'
    },
    {
        'src': 'http://91130b1325445faefa46-0a57a58cc8418ee081f89836dd343dea.r74.cf1.rackcdn.com/magento_web_files.tar.gz',
        'dst': '/srv/salt/magento/files/web_files.tar.gz'
    },
    {
        'src': 'http://91130b1325445faefa46-0a57a58cc8418ee081f89836dd343dea.r74.cf1.rackcdn.com/gatling-charts-highcharts-2.0.0-M3a-bundle.tar.gz',
        'dst': '/srv/salt/gatling/files/gatling-charts-highcharts-2.0.0-M3a-bundle.tar.gz'
    }
]


def post_download(cls):
    """
    Decorator that post install downloads files.

    """
    old_run = cls.run

    def new_run(self):
        old_run(self)
        downloader = PostInstallDownloader()
        downloader.download_many(post_install_download_files)

    cls.run = new_run
    return cls


@post_download
class PostDownloadInstall(install):
    pass


@post_download
class PostDownloadDevelop(develop):
    pass
