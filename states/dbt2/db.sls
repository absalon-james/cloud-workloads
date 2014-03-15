{% from "dbt2/db.jinja" import dbt2 with context %}

include:
  - mysql.mysql

mysql-user-{{ dbt2.user }}:
 
  mysql_database.present:
    - name: {{ dbt2.database }}

  mysql_user.present:
    - name: {{ dbt2.user }}
    - password: {{ dbt2.password }}
    - host: {{ dbt2.host }}

  mysql_grants.present:
    - user: {{ dbt2.user }}
    - host: {{ dbt2.host }}
    - database: '{{ dbt2.database }}.*'
    - grant: all 
