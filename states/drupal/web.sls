apache2:
  pkg:
    - name: apache2
    - installed

php5:
  pkg:
    - name: php5
    - installed

php5-mysql:
  pkg:
    - name: php5-mysql
    - installed

php5-gd:
  pkg:
    - name: php5-gd
    - installed

php5-apc:
  pkg:
    - name: php-apc
    - installed

memcached:
  pkg:
    - name: memcached
    - installed

libmemcached-tools:
  pkg:
    - name: libmemcached-tools
    - installed

php5-dev:
  pkg:
    - name: php5-dev
    - installed

php-pear:
  pkg:
    - name: php-pear
    - installed

make:
  pkg:
    - name: make
    - installed

pecl_memcache:
  pecl.installed:
    - name: memcache

/var/www/index.html:
  file.absent:
    - name: /var/www/index.html

drupal_archive:
  file.managed:
    - name: /var/drupal_web.tar.gz
    - source: salt://drupal/files/drupal_web.tar.gz

unzip_archive:
  cmd.wait:
    - name: tar -zxvf drupal_web.tar.gz
    - cwd: /var/
    - watch:
      - file: drupal_archive

/var/www:
  file.directory:
    - user: www-data
    - group: www-data
    - mode: 755
    - recurse:
      - user
      - group
      - mode

/var/www/sites/default/settings.php:
  file.managed:
    - name: /var/www/sites/default/settings.php
    - source: salt://drupal/files/drupal_settings.php
    - template: jinja
    - user: www-data
    - group: www-data
    - mode: 755

php_memcache_ini:
  file.managed:
    - name: /etc/php5/conf.d/memcache.ini
    - source: salt://drupal/files/php-memcache.ini

memcached_conf:
  file.managed:
    - name: /etc/memcached.conf
    - source: salt://drupal/files/memcached.conf
    - template: jinja

apache-service:
  service:
    - name: apache2
    - running
    - watch:
      - file: php_memcache_ini
      - pecl: pecl_memcache

memcached-service:
  service:
    - name: memcached
    - running
    - watch:
      - file: memcached_conf
      - pecl: pecl_memcache


