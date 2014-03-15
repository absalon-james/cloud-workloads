{% from "magento/db.jinja" import magento with context %}
include:
  - mysql.mysql

magento_db_user:

  mysql_user.present:
    - name:     {{ magento.db_user }}
    - password: {{ magento.db_password }}
    - host:     {{ magento.db_host }}

  mysql_grants.present:
    - user: {{ magento.db_user }}
    - host: {{ magento.db_host }}
    - database: {{ magento.db_name }}.*
    - grant: all

{% if magento.master %}
stop_slave:
  cmd.run:
    - name: mysql -uroot --password="" -e "STOP SLAVE"

change_master:
  cmd.run:
    - name: mysql -uroot --password="" -e "CHANGE MASTER TO MASTER_HOST='{{ magento.master }}', MASTER_USER='{{ magento.slave_user }}', MASTER_PASSWORD='{{ magento.slave_password }}';"

dump_master:
  cmd.run:
    - name: mysqldump -h{{ magento.master }} -u{{ magento.slave_user }} -p{{ magento.slave_password }} --add-drop-database --add-drop-table --master-data --databases {{ magento.db_name }} > /opt/magento.db

load_dump:
  cmd.wait:
    - name: mysql -uroot --password="" < /opt/magento.db
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
