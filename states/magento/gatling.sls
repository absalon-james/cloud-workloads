{% from 'gatling/settings.sls' import gatling with context %}

{% set simulation_tar = "gatling.simulations.magento.tar.gz" %}

include:
  - gatling

/opt/{{ gatling.dir }}/user-files/data/buyers.csv:
  file.managed:
    - source: salt://magento/files/gatling-buyers.csv

/opt/{{ gatling.dir }}/user-files/simulations/{{ simulation_tar }}:
  file.managed:
    - source: salt://magento/files/{{ simulation_tar }}

tar -zxf {{ simulation_tar }}:
  cmd.watch:
    - cwd: /opt/{{ gatling.dir }}/user-files/simulations/
    - watch:
      - file: /opt/{{ gatling.dir }}/user-files/simulations/{{ simulation_tar }}
