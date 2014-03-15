{% from "primitives/init.sls" import primitives_dir with context %}
{% set filebench = "filebench-1.4.9.1" %}

include:
  - primitives
 
configure filebench:
  cmd.run:
    - name: ./configure
    - cwd: {{ primitives_dir }}/{{ filebench }}

make filebench:
  cmd.run:
    - name: make
    - cwd: {{ primitives_dir }}/{{ filebench }}
    - require:
      - cmd: configure filebench

install filebench:
  cmd.run:
    - name: make install
    - cwd: {{ primitives_dir }}/{{ filebench }}
    - require:
      - cmd: make filebench

enable workloads:
  cmd.run:
    - name: echo "run 60" | tee -a *.f
    - cwd: {{ primitives_dir }}/{{ filebench }}/workloads
