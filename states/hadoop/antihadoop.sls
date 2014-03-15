{%- from 'hadoop/settings.sls' import hadoop with context %}

services:
  service:
    - dead
    - enable: False
    - sig: hadoop
    - names:
      - hadoop-secondarynamenode
      - hadoop-namenode
      - hadoop-datanode
      - hadoop-jobtracker
      - hadoop-tasktracker

leftovers:
  cmd.run:
    - name: pkill -f hadoop

{%- set hdfs_disks = salt['grains.get']('hdfs_data_disks', ['/data']) %}
{% set mapred_disks = salt['pillar.get']('mapred_data_disks', ['/data']) %}
{%- set hadoop_users = hadoop.get('users', {}) %}

{% if (hadoop['major_version'] == '1') and not hadoop.cdhmr1 %}
{% set real_config_src = hadoop['real_home'] + '/conf' %}
{% else %}
{% set real_config_src = hadoop['real_home'] + '/etc/hadoop' %}
{% endif %}

hadoop-home-link:
  alternatives.remove:
    - path: {{ hadoop['real_home'] }}

hadoop-conf-link:
  alternatives.remove:
    - path: {{ hadoop['real_config'] }}

remove-files:
  file.absent:
    - names:
      - /var/log/hadoop
      - /var/run/hadoop
      - /var/lib/hadoop
      - /usr/lib/hadoop*
      - {{ hadoop['real_home'] }}/lib
      - {{ hadoop.alt_home }}
      - /etc/profile.d/hadoop.sh
      - /etc/hadoop
      - {{ hadoop['real_config'] }}
      - {{ hadoop.real_config_dist }}
      - {{ real_config_src }}
      - {{ hadoop['alt_config'] }}
      - /etc/init.d/hadoop-namenode
      - /etc/init.d/hadoop-secondarynamenode
      - /etc/init.d/hadoop-datanode
      - /etc/init.d/hadoop-jobtracker
      - /etc/init.d/hadoop-tasktracker
{% for disk in hdfs_disks %}
      - {{ disk }}/hdfs
{% endfor %}
{% for disk in mapred_disks %}
      - {{ disk }}/mapred
{% endfor %}
{%- if grains.os == 'Ubuntu' %}
      - /etc/default/hadoop
{%- endif %}

vm.swappiness:
  sysctl:
    - present
    - value: 0

hdfs-user:
  user.absent:
    - name: hdfs
    - purge: True

mapred-user:
  user.absent:
    - name: 'mapred'
    - purge: True

hadoop:
  group.absent:
    - gid: {{ hadoop_users.get('hadoop', '6000') }}
