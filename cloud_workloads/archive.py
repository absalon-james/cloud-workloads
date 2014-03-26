import os
import shutil
import time


class HtmlArchive(object):
    """
    Class for archiving data results. Will create symlinks to the
    most current result, other results will still be accessible
    via the archives.

    The end goal is to have a tree similar to:
    |--<basedir>
       |--latest.html(symlink to newestdate/index.html)
       |--asset1.js
       |--asset2.js
       |--asset3.css
       |--achive
          |--<oldestdate>
             |--index.html
             |--asset1.js
             |--asset2.js
             |--asset3.css
          |--<olderdate>
             |--index.html
             |--asset1.js
             |--asset2.js
             |--asset3.css
          |--<newestdate>
             |--index.html
             |--asset1.js
             |--asset2.js
             |--asset3.css
    """
    time_format = '%y-%m-%d--%H-%M-%S'

    def __init__(self, basedir):
        """
        Initializer

        @param basedir - Output directory to contain the archive

        """
        self.basedir = basedir

        # Make sure directory exists
        self.create_dir(self.basedir)

        # Create directory index via .htaccess
        self.create_dir_index(self.basedir)

        # Make sure subdirectory exists
        self.create_dir(os.path.join(self.basedir, 'archive'))

        # Get and copy assets
        self.assets = self.get_assets()

    def create_dir(self, newdir):
        """
        Checks to see if newdir already exists. Raises error if it is a file.
        If it is already a directory, do nothing we are done.
        If it does not exists, try to create it.

        @param newdir - String directory to create
        """
        if os.path.isfile(newdir):
            raise Exception(
                "Cannot create directory %s. File %s already exists."
                % (newdir, newdir)
            )

        # Check to see if newdir exists,
        if os.path.isdir(newdir):
            return True

        # If not a file, and not a directory, try to create the directory
        # Let os errors bubble out
        os.makedirs(newdir, 0755)

    def create_dir_index(self, dir_):
        """
        Creates the .htaccess file for displaying directory indexes

        @param dir_ directory to add .htaccess to.

        """
        filename = os.path.join(dir_, ".htaccess")
        if not os.path.isfile(filename):
            htaccess_str = "Options +Indexes"
            with open(filename, 'w') as f:
                f.write(htaccess_str)

    def get_assets(self):
        """
        Builds a list of assets.  An asset is a file in the assets directory.
        We should include full file name.

        @return - List of dictionaries describing assets

        """
        assets = []
        assets_dir = os.path.join(os.path.dirname(__file__), 'assets')
        for filename in os.listdir(assets_dir):
            abspath = os.path.abspath(os.path.join(assets_dir, filename))
            if os.path.isfile(abspath):
                assets.append({
                    'filename': filename,
                    'abspath': abspath
                })
        return assets

    def archive(self, text):
        """
        Creates a timestamped directory to store text as index.html

        @param text - String html to write to index.html

        """
        # Create directory to contain the real results.
        dirname = time.strftime(self.time_format)
        resultdir = os.path.join(self.basedir, 'archive', dirname)
        self.create_dir(resultdir)

        # Write text to index.html
        filename = os.path.join(resultdir, 'index.html')
        with open(filename, 'w') as f:
            f.write(text)

        # Copy js and css assets to resultdir
        self.copy_assets(self.assets, resultdir)

        # Create symlink from basedir/latest.html to index.html
        link = os.path.join(self.basedir, 'latest.html')
        if os.path.islink(link):
            os.unlink(link)
        os.symlink(filename, link)

        # Copy assets to base directory
        self.copy_assets(self.assets, self.basedir)

    def copy_assets(self, assets, targetdir):
        """
        Copy assets over to the output directory, then create symlinks to them
        in the archive directory

        @param assets - List of dicts describing assets

        """

        for asset in assets:
            dst = os.path.join(targetdir, asset['filename'])
            src = asset['abspath']
            shutil.copyfile(src, dst)
