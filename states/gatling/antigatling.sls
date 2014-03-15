{% from 'gatling/settings.sls' import gatling with context %}

gatling-files:
  file.absent:
    - names:
      - /opt/{{ gatling.tar }}
      - /opt/{{ gatling.tar_dir }}
      - /opt/{{ gatling.dir }}

gatling-user:
  user.absent:
    - name: gatling
