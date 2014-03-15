{% from "drupal/db.jinja" import drupal with context %}

# Include standard mysql config
include:
  - mysql.mysql

# Set up the user for replication to this master
drupal_slave_user:
  # Create the user
  mysql_user.present:
    - name:     {{ drupal.slave_user }}
    - password: {{ drupal.slave_password }}
    - host:     {{ drupal.slave_host }}
  # Assign permissions
  mysql_grants.present:
    - user: {{ drupal.slave_user }}
    - host: {{ drupal.slave_host }}
    - database: '*.*'
    - grant: replication slave, reload, replication client, select

# Set up the database user drupal will use
drupal_db_user:
  # Create the user
  mysql_user.present:
    - name:     {{ drupal.db_user }}
    - password: {{ drupal.db_password }}
    - host:     {{ drupal.db_host }}
  # Assign permissions
  mysql_grants.present:
    - user:     {{ drupal.db_user }}
    - host:     {{ drupal.db_host }}
    - database: 'drupal_bench.*'
    - grant: select, insert, update, delete, create, drop, index, alter, lock tables, create temporary tables

# Provide compressed starting master database
drupal_db_archive:
  file.managed:
    - name: /opt/drupal.db.tar.gz
    - source: salt://drupal/files/drupal.db.tar.gz
    - makedirs: True

# Unzip the master archive
drupal_db_unzip:
  cmd.wait:
    - name: tar -zxvf drupal.db.tar.gz
    - cwd: /opt/
    - watch:
      - file: drupal_db_archive

# Load the database
load_dump:
  cmd.wait:
    - name: mysql -uroot --password="" < /opt/drupal.db
    - watch:
      - cmd: drupal_db_unzip
