{% from "primitives/init.sls" import primitives_dir with context %}

# Iperf server may be left over
#pkill -f iperf:
#  cmd:
#    - run

{{ primitives_dir }}:
  file:
    - absent
