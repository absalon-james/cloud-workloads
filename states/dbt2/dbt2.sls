{% from "dbt2/db.jinja" import dbt2 with context %} 

requirements:
  pkg.installed:
    - pkgs:
      - gcc
      - make
      - build-essential
      - liblocal-lib-perl
      - libexpat1-dev
      - libmysqlclient-dev
      - mysql-client

/etc/mysql/my.cnf:
  file.managed:
    - name: /etc/mysql/my.cnf
    - source: salt://dbt2/files/my.cnf

cpan:
  cmd.run:
    - name: cpan

perl-statistics-descriptive:
  cmd.wait:
    - name: cpan install Statistics::Descriptive
    - watch:
      - cmd: cpan

perl-test-parser:
  cmd.run:
    - name: cpan install Test::Parser

perl-test-reporter:
  cmd.run:
    - name: cpan install Test::Reporter

/opt/dbt2.tar.gz:
  file.managed:
    - name: /opt/dbt2.tar.gz
    - source: salt://dbt2/files/dbt2.tar.gz

dbt2-unzip:
  cmd.wait:
    - name: tar -zxvf dbt2.tar.gz
    - cwd: /opt/
    - watch:
      - file: /opt/dbt2.tar.gz

dbt2-configure:
  cmd.wait:
    - name: ./configure --with-mysql
    - cwd: /opt/dbt2-0.37.50.3/
    - watch:
      - cmd: dbt2-unzip

dbt2-make:
  cmd.wait:
    - name: make
    - cwd: /opt/dbt2-0.37.50.3/
    - watch:
      - cmd: dbt2-configure

dbt2-make-install:
  cmd.wait:
    - name: make install
    - cwd: /opt/dbt2-0.37.50.3/
    - watch:
      - cmd: dbt2-make

/opt/dbt2-0.37.50.3/scripts/mysql/mysql_load_db.sh:
  file.managed:
    - name: /opt/dbt2-0.37.50.3/scripts/mysql/mysql_load_db.sh
    - source: salt://dbt2/files/mysql_load_db.sh
    - template: jinja

/opt/dbt2-0.37.50.3/scripts/mysql/mysql_load_sp.sh:
  file.managed:
    - name: /opt/dbt2-0.37.50.3/scripts/mysql/mysql_load_sp.sh
    - source: salt://dbt2/files/mysql_load_sp.sh
    - template: jinja

/opt/data/:
  file.directory:
    - name: /opt/data
    - makdirs: True

create-data:
  cmd.run:
    - name: datagen -w {{ dbt2.warehouses }} -d /opt/data --mysql

load-db:
  cmd.wait:
    - name: /opt/dbt2-0.37.50.3/scripts/mysql/mysql_load_db.sh --path /opt/data/ --mysql-path /usr/bin/mysql --database {{ dbt2.database }} --user {{ dbt2.user }} --host {{ dbt2.location }} --local
    - watch:
      - cmd: create-data

load-sp:
  cmd.wait:
    - name: /opt/dbt2-0.37.50.3/scripts/mysql/mysql_load_sp.sh --client-path /usr/bin/ --sp-path /opt/dbt2-0.37.50.3/storedproc/mysql --host {{ dbt2.location }} --user {{ dbt2.user }}
    - watch:
      - cmd: load-db

