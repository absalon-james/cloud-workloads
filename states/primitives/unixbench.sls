{% from "primitives/init.sls" import primitives_dir with context %}
{% set unixbench_dir = "UnixBench" %}

include:
  - primitives

libjson-perl:
  pkg:
    - installed
 
make unixbench:
  cmd.run:
    - name: make
    - cwd: {{ primitives_dir }}/{{ unixbench_dir }}

{{ primitives_dir }}/{{ unixbench_dir }}/Run:
  file.managed:
    - source: salt://primitives/files/Run
    - mode: 744 
