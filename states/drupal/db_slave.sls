{% from "drupal/db.jinja" import drupal with context %}
include:
  - mysql.mysql

drupal_db_user:

  mysql_user.present:
    - name:     {{ drupal.db_user }}
    - password: {{ drupal.db_password }}
    - host:     {{ drupal.db_host }}

  mysql_grants.present:
    - user: {{ drupal.db_user }}
    - host: {{ drupal.db_host }}
    - database: drupal_bench.*
    - grant: select, insert, update, delete, create, drop, index, alter, lock tables, create temporary tables

{% if drupal.master %}
stop_slave:
  cmd.run:
    - name: mysql -uroot --password="" -e "STOP SLAVE"

change_master:
  cmd.run:
    - name: mysql -uroot --password="" -e "CHANGE MASTER TO MASTER_HOST='{{ drupal.master }}', MASTER_USER='{{ drupal.slave_user }}', MASTER_PASSWORD='{{ drupal.slave_password }}';"

dump_master:
  cmd.run:
    - name: mysqldump -h{{ drupal.master }} -u{{ drupal.slave_user }} -p{{ drupal.slave_password }} --add-drop-database --add-drop-table --master-data --databases drupal_bench > /opt/drupal.db

load_dump:
  cmd.wait:
    - name: mysql -uroot --password="" < /opt/drupal.db
    - watch:
      - cmd: dump_master

start_slave:
  cmd.wait:
    - name: mysql -uroot --password="" -e "START SLAVE"
    - watch:
      - cmd: load_dump

check_status:
  cmd.wait:
    - name: mysql -uroot --password="" -e "SHOW SLAVE STATUS\G"
    - watch:
      - cmd: start_slave
{% endif %}
