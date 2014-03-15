requirements:
  pkg.purged:
    - pkgs:
      - gcc
      - make
      - build-essential
      - liblocal-lib-perl
      - libexpat1-dev
      - libmysqlclient-dev
      - mysql-client
      - mysql-common

/opt/dbt2.tar.gz:
  file.absent:
    - name: /opt/dbt2.tar.gz

/opt/dbt2-0.37.50.3:
  file.absent:
    - name: /opt/dbt2-0.37.50.3

/opt/data:
  file.absent:
    - name: /opt/data

#make-install:
#  cmd.wait:
#    - name: make install
#    - cwd: /opt/dbt2-0.37.50.3/
#    - watch:
#      - cmd: make

/etc/mysql:
  file.absent:
    - name: /etc/mysql

/var/lib/mysql:
  file.absent:
    - name: /var/lib/mysql

/var/log/mysql:
  file.absent:
    - name: /var/log/mysql

/root/output:
  file.absent:
    - name: /root/output


