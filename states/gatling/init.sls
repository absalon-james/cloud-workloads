{% from 'gatling/settings.sls' import gatling with context %}

include:
  - java

gatling-user:
  user.present:
    - name: gatling

/opt/{{ gatling.tar }}:
  file.managed:
    - source: salt://gatling/files/{{ gatling.tar }}

unpack-gatling:
  cmd.wait:
    - name: tar -zxf {{ gatling.tar }}
    - cwd: /opt/
    - watch:
      - file: /opt/{{ gatling.tar }}

mv /opt/{{ gatling.tar_dir }} /opt/{{ gatling.dir }}:
  cmd.wait:
    - watch:
      - cmd: unpack-gatling

/opt/{{ gatling.dir }}:
  file.directory:
    - user: gatling
    - recurse:
      - user
