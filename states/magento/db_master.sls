{% from "magento/db.jinja" import magento with context %}

# Include standard mysql config
include:
  - mysql.mysql

# Set up the user for replication to this master
magento_slave_user:
  # Create the user
  mysql_user.present:
    - name:     {{ magento.slave_user }}
    - password: {{ magento.slave_password }}
    - host:     {{ magento.slave_host }}
  # Assign permissions
  mysql_grants.present:
    - user: {{ magento.slave_user }}
    - host: {{ magento.slave_host }}
    - database: '*.*'
    - grant: replication slave, reload, replication client, select

magento_db:
  mysql_database.present:
    - name: {{ magento.db_name }}

# Set up the database user magento will use
magento_db_user:
  # Create the user
  mysql_user.present:
    - name:     {{ magento.db_user }}
    - password: {{ magento.db_password }}
    - host:     {{ magento.db_host }}
  # Assign permissions
  mysql_grants.present:
    - user:     {{ magento.db_user }}
    - host:     {{ magento.db_host }}
    - database: '{{ magento.db_name }}.*'
    - grant: all

# Provide compressed starting master database
magento_sample_data:
  file.managed:
    - name: /opt/magento/sample-data.sql
    - source: salt://magento/files/sample-data.sql
    - makedirs: True

# Load the database
load_sample_data:
  cmd.wait:
    - name: mysql -uroot --password="" {{ magento.db_name }} < /opt/magento/sample-data.sql
    - watch:
      - file: magento_sample_data
