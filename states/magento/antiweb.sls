requirements:
  pkg.purged:
    - pkgs:
      - apache2
      - apache2-utils
      - apache2.2-bin
      - apache2-common
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
      - mysql-common
      - memcached
      - libmemcached-tools

/var/www:
  file.absent:
    - name: /var/www

/etc/php5:
  file.absent:
    - name: /etc/php5

/etc/apache2:
  file.absent:
    - name: /etc/apache2

/etc/memcached.conf:
  file.absent:
    - name: /etc/memcached.conf
