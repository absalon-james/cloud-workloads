requirements:
  pkg.installed:
    - pkgs:
      - apache2
      - memcached
      - php5
      - php5-common
      - php5-mcrypt
      - php5-curl
      - php5-cli
      - php5-mysql
      - php5-gd
      - php5-memcached
      - php5-dev
      - php-apc

web_files:
  file.managed:
    - name: /var/www/web_files.tar.gz
    - source: salt://magento/files/web_files.tar.gz
    - makedirs: True

unzip_web_files:
  cmd.wait:
    - name: tar -zxvf web_files.tar.gz
    - cwd: /var/www/
    - watch:
      - file: web_files

web_files_permissions:
  file.directory:
    - name: /var/www/magento
    - user: www-data
    - group: www-data
    - mode: 755
    - recurse:
      - user
      - group
      - mode
    - watch:
      - cmd: unzip_web_files

/etc/php5/apache2/php.ini:
  file.managed:
    - name: /etc/php5/apache2/php.ini
    - source: salt://magento/files/php.ini
    - template: jinja

/etc/apache2/sites-available/default:
  file.managed:
    - name: /etc/apache2/sites-available/default
    - source: salt://magento/files/apache-default
    - template: jinja

/etc/memcached.conf:
  file.managed:
    - name: /etc/memcached.conf
    - source: salt://magento/files/memcached.conf
    - template: jinja

magento-config:
  file.managed:
    - name: /var/www/magento/app/etc/config.xml
    - source: salt://magento/files/magento-config.xml
    - user: www-data
    - group: www-data
    - mode: 755
    - template: jinja

magento-local-config:
  file.managed:
    - name: /var/www/magento/app/etc/local.xml
    - source: salt://magento/files/magento-local-config.xml
    - user: www-data
    - group: www-data
    - mode: 755
    - template: jinja

apache-service:
  service:
    - name: apache2
    - running
    - watch:
      - file: /etc/php5/apache2/php.ini
      - file: /etc/memcached.conf

memcached-service:
  service:
    - name: memcached
    - running
    - watch:
      - file: /etc/memcached.conf

#php_memcache_ini:
#  file.managed:
#    - name: /etc/php5/conf.d/memcache.ini
#    - source: salt://drupal/files/php-memcache.ini
