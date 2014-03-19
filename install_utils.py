import os


def find_data_files(starting_path, prefix):
    """
    Traverses the directory starting at starting path
    finding all subdirectories and files.  Useful when
    building complex data_files list. Strips off the first
    directory and replaces with prefix
    Example:
        prefix = '/srv/pillar'
        path = 'pillar/drupal
        fixed path will be /srv/pillar/drupal

        prfix = /srv/salt
        path = states/drupal
        fixed parth will be /srv/salt/drupal

    @param starting_path - String starting path
    @param prefix - String prefix to prepend to each file path

    """
    data_files = []
    for path, dirs, files in os.walk(starting_path):
        files = [os.path.join(path, f) for f in files]
        start, _, rest = path.partition(os.path.sep)
        data_files.append((os.path.join(prefix, rest), files))
    return data_files


def readme():
    """
    Returns contents of README.md

    @return - String

    """
    with open('README.md') as f:
        return f.read()
