mysql-software:
  pkg.installed:
    - pkgs:
      - python-mysqldb
      - mysql-server

/etc/mysql/my.cnf:
  file.managed:
    - name: /etc/mysql/my.cnf
    - template: jinja
    - source: salt://mysql/files/mysql.cnf
    - user: root
    - group: root
    - mode: 644

mysql-server:

  innodb:
    - fix_logs
    
  service:
    - running
    - name: mysql
    - watch:
      - file: /etc/mysql/my.cnf
