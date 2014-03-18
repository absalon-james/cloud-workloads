{% set p  = salt['pillar.get']('java', {}) %}
{% set g  = salt['grains.get']('java', {}) %}

{%- set java_home      = salt['grains.get']('java_home', salt['pillar.get']('java_home', '/usr/lib/java')) %}
{%- set java_real_home = '/usr/lib/jvm/java-7-openjdk-amd64' %}

{%- set java = {} %}
{%- do java.update({
    'java_home': java_home,
    'java_real_home' : java_real_home
}) %}
