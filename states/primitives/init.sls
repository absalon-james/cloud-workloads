# TODO - Pull from pillar
{% set primitives_dir = "/opt/primitives" %}
{% set iperf_dir = "iperf-2.0.5" %}
{% set filebench = "filebench-1.4.9.1" %}
{% set unixbench_dir = "UnixBench" %}


required-software:
  pkg.installed:
    - pkgs:
      - build-essential
      - gcc

{{ primitives_dir }}:
  file.recurse:
    - source: salt://primitives/files/src

Run untar:
  cmd.run:
    - name: for i in *gz; do tar -xzvf $i; done
    - cwd: {{ primitives_dir }}
    - require:
      - file: {{ primitives_dir }}

###############
### Iperf #####
###############
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

###############
## FileBench ##
###############
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

###############
## UnixBench ##
###############
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
