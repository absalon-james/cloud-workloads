{% from "dbt2/db.jinja" import dbt2 with context %}

run:
  cmd.run:
    - name: /opt/dbt2-0.37.50.3/scripts/run_mysql.sh --connections {{ dbt2.connections }} --warehouses {{ dbt2.warehouses }} --time {{ dbt2.duration }} --host {{ dbt2.location }} --database {{ dbt2.database }} --user {{ dbt2.user }} --password {{ dbt2.password }} --zero-delay --lib-client-path /usr/bin/mysql
