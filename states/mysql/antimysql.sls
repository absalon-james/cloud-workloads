# Remove packages
uninstall-packages:
  pkg.purged:
    - pkgs:
      - python-mysqldb
      - mysql-server
      - mysql-client
      - mysql-common

/etc/mysql/:
  file.absent:
    - name: /etc/mysql

/var/lib/mysql:
  file.absent:
    - name: /var/lib/mysql

/var/log/mysql:
  file.absent:
    - name: /var/log/mysql
