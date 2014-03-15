{% from 'gatling/settings.sls' import gatling with context %}

{% set simulation_tar = "gatling.simulations.drupal.tar.gz" %}

include:
  - gatling

/opt/{{ gatling.dir }}/user-files/data/user_credentials.csv:
  file.managed:
    - source: salt://drupal/files/gatling-users.csv

/opt/{{ gatling.dir }}/user-files/simulations/{{ simulation_tar }}:
  file.managed:
    - source: salt://drupal/files/{{ simulation_tar }}

tar -zxf {{ simulation_tar }}:
  cmd.watch:
    - cwd: /opt/{{ gatling.dir }}/user-files/simulations/
    - watch:
      - file: /opt/{{ gatling.dir }}/user-files/simulations/{{ simulation_tar }}
