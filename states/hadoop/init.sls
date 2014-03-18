include:
  - hostsfile.hostname
  - hostsfile
  - ntp.server
  - java
  - java.env

{%- from 'hadoop/settings.sls' import hadoop with context %}
# TODO: no users implemented in settings yet
{%- set hadoop_users = hadoop.get('users', {}) %}

hadoop:
  group.present:
    - gid: {{ hadoop_users.get('hadoop', '6000') }}
  file.directory:
    - user: root
    - group: hadoop
    - mode: 775
    - names:
      - /var/log/hadoop
      - /var/run/hadoop
      - /var/lib/hadoop
    - require:
      - group: hadoop

vm.swappiness:
  sysctl:
    - present
    - value: 10

vm.overcommit_memory:
  sysctl:
    - present
    - value: 0

unpack-hadoop-dist:
  cmd.run:
    - name: curl '{{ hadoop.source_url }}' | tar xz
    - cwd: /usr/lib
    - unless: test -d {{ hadoop['real_home'] }}/lib

hadoop-home-link:
  alternatives.install:
    - link: {{ hadoop['alt_home'] }}
    - path: {{ hadoop['real_home'] }}
    - priority: 30
    - require:
#      - cmd.run: unpack-hadoop-dist
      - cmd: unpack-hadoop-dist

{{ hadoop['real_home'] }}:
  file.directory:
    - user: root
    - group: root
    - recurse:
      - user
      - group
    - require:
#      - cmd.run: unpack-hadoop-dist
      - cmd: unpack-hadoop-dist

{%- if hadoop.cdhmr1 %}

{{ hadoop.alt_home }}/share/hadoop/mapreduce:
  file.symlink:
    - target: {{ hadoop.alt_home }}/share/hadoop/mapreduce1
    - force: True

rename-bin:
  cmd.run:
    - name: mv {{ hadoop.alt_home }}/bin {{ hadoop.alt_home }}/bin-mapreduce2
    - unless: test -L {{ hadoop.alt_home }}/bin

rename-config:
  cmd.run:
    - name: mv {{ hadoop.alt_home }}/etc/hadoop {{ hadoop.alt_home }}/etc/hadoop-mapreduce2
    - unless: test -L {{ hadoop.alt_home }}/etc/hadoop

{{ hadoop.alt_home }}/bin:
  file.symlink:
    - target: {{ hadoop.alt_home }}/bin-mapreduce1
    - force: True

{{ hadoop.alt_home }}/etc/hadoop:
  file.symlink:
    - target: {{ hadoop.alt_home }}/etc/hadoop-mapreduce1
    - force: True

{% endif %}

/etc/profile.d/hadoop.sh:
  file.managed:
    - source: salt://hadoop/files/hadoop.sh.jinja
    - template: jinja
    - mode: 644
    - user: root
    - group: root
    - context:
      hadoop_config: {{ hadoop['alt_config'] }}

{% if (hadoop['major_version'] == '1') and not hadoop.cdhmr1 %}
{% set real_config_src = hadoop['real_home'] + '/conf' %}
{% else %}
{% set real_config_src = hadoop['real_home'] + '/etc/hadoop' %}
{% endif %}

/etc/hadoop:
  file.directory:
    - user: root
    - group: root
    - mode: 755

move-hadoop-dist-conf:
  file.directory:
    - name: {{ hadoop['real_config'] }}
    - user: root
    - group: root
  cmd.run:
    - name: mv  {{ real_config_src }} {{ hadoop.real_config_dist }}
    - unless: test -d {{ hadoop.real_config_dist }}
    - onlyif: test -d {{ real_config_src }}
    - require:
      - file: {{ hadoop['real_home'] }}
      - file: /etc/hadoop
      #- file.directory: {{ hadoop['real_home'] }}
      #- file.directory: /etc/hadoop

{{ real_config_src }}:
  file.symlink:
    - target: {{ hadoop['alt_config'] }}
    - require:
      - cmd: move-hadoop-dist-conf

hadoop-conf-link:
  alternatives.install:
    - link: {{ hadoop['alt_config'] }}
    - path: {{ hadoop['real_config'] }}
    - priority: 30
    - require:
#      - file.directory: {{ hadoop['real_config'] }}
      - file: move-hadoop-dist-conf

{{ hadoop['real_config'] }}/log4j.properties:
  file.copy:
    - source: {{ hadoop['real_config_dist'] }}/log4j.properties
    - user: root
    - group: root
    - mode: 644
    - require:
      - file: {{ hadoop['real_config'] }}
#      - alternatives.install: hadoop-conf-link
      - alternatives: hadoop-conf-link

{{ hadoop['real_config'] }}/hadoop-env.sh:
  file.managed:
    - source: salt://hadoop/conf/hadoop-env.sh
    - template: jinja
    - mode: 644
    - user: root
    - group: root
    - context:
      #java_home: {{ salt['pillar.get']('java_home', '/usr/lib/java') }}
      java_home: {{ salt['pillar.get']('java_home', '/usr/lib/jvm/java-7-openjdk-amd64') }}
      hadoop_home: {{ hadoop['alt_home'] }}
      hadoop_config: {{ hadoop['alt_config'] }}

{%- if grains.os == 'Ubuntu' %}
/etc/default/hadoop:
  file.managed:
    - source: salt://hadoop/files/hadoop.jinja
    - mode: '644'
    - template: jinja
    - user: root
    - group: root
    - context:
      #java_home: {{ salt['pillar.get']('java_home', '/usr/lib/java') }}
      java_home: {{ salt['pillar.get']('java_home', '/usr/lib/jvm/java-7-openjdk-amd64') }}
      hadoop_home: {{ hadoop['alt_home'] }}
      hadoop_config: {{ hadoop['alt_config'] }}
{%- endif %}
