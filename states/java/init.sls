{%- from 'java/settings.sls' import java with context %}

openjdk-7-jdk:
  pkg.installed

alternatives:
  alternatives.install:
    - name: java-home-link
    - link: {{ java.java_home }}
    - path: {{ java.java_real_home }}
    - priority: 30
    - require:
      - pkg: openjdk-7-jdk
