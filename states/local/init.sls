requirements:
  pkg.installed:
    - pkgs:
      - gcc
      - apache2
      - python-dev
      - python-pip
      - salt-ssh

/etc/salt/master:
  file.managed:
    - source: salt://local/files/master

salt-master:
  service.running:
    - enable: True
    - watch:
      - file: /etc/salt/master

/tmp/cloud-workloads.tar.gz:
  file.managed:
    - source: http://91130b1325445faefa46-0a57a58cc8418ee081f89836dd343dea.r74.cf1.rackcdn.com/cloud_workloads-0.1.tar.gz
    - source_hash: md5=b17cfc11999160bf09de565016a2a3df

pip install --upgrade /tmp/cloud-workloads.tar.gz:
  cmd.run:
    - require:
      - file: /tmp/cloud-workloads.tar.gz
