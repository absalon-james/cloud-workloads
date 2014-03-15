pecl-installed-software:
  pecl.removed:
    - name: memcache

intalled-software:
  pkg.purged:
    - pkgs:
      - apache2
      - apache2-utils
      - apache2.2-bin
      - apache2-common
      - php5
      - php5-cli
      - php5-common
      - php5-mysql
      - php5-gd
      - php5-dev
      - php-apc
      - mysql-common
      - memcached
      - libmemcached-tools
      - php-pear

/var/drupal_web.tar.gz:
  file.absent:
    - name: /var/drupal_web.tar.gz

/var/www:
  file.absent:
    - name: /var/www

/etc/php5:
  file.absent:
    - name: /etc/php5

/etc/memcached.conf:
  file.absent:
    - name: /etc/memcached.conf
