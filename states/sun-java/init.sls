{%- from 'sun-java/settings.sls' import java with context %}

# require a source_url - there is no default download location for a jdk
{%- if java.source_url is defined %}

{{ java.prefix }}:
  file.directory:
    - user: root
    - group: root
    - mode: 755

get-jdk-tarball:
  file.managed:
    - name: {{ java.prefix }}/{{ java.version_name }}.tar.gz
    - source: {{ java.source_url }}
    - require:
#      - file.directory: {{ java.prefix }}
      - file: {{ java.prefix }}

unpack-jdk-tarball:
#  cmd.run:
#    - name: curl {{ java.dl_opts }} '{{ java.source_url }}' | tar xz
#    - cwd: {{ java.prefix }}
#    - unless: test -d {{ java.java_real_home }}
#    - require:
#      - file.directory: {{ java.prefix }}

  cmd.wait:
    - name: tar -zxf {{ java.version_name }}.tar.gz
    - cwd: {{ java.prefix }}
    - watch:
      - file: get-jdk-tarball

  alternatives.install:
    - name: java-home-link
    - link: {{ java.java_home }}
    - path: {{ java.java_real_home }}
    - priority: 30
    - require:
      - file: {{ java.prefix }}
#      - file.directory: {{ java.prefix }}

{%- endif %}
