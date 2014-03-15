# Drupal database specific information
# Shown with defaults
drupal:
  # Database user drupal will use to connect to mysql
  db:
    user: drupal_bench
    password: drupal_bench
    host: "'%'"
    interface: eth0

  # Database user a replication slave will use to connect to mysql
  slave:
    user: drupal_slave
    password: drupal_slave
    host: "'%'"


#  master: 23.253.83.115
#  slaves:
#    - 23.253.83.226
