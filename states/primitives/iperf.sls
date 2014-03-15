{% from "primitives/init.sls" import primitives_dir with context %}
{% set iperf_dir = "iperf-2.0.5" %}

include:
  - primitives
 
configure iperf:
  cmd.run:
    - name: ./configure
    - cwd: {{ primitives_dir }}/{{ iperf_dir }}

make iperf:
  cmd.run:
    - name: make
    - cwd: {{ primitives_dir }}/{{ iperf_dir }}
    - require:
      - cmd: configure iperf

install iperf:
  cmd.run:
    - name: make install
    - cwd: {{ primitives_dir}}/{{ iperf_dir }}
    - require:
      - cmd: make iperf
