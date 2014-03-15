{% from "dbt2/db.jinja" import dbt2 with context %}

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
