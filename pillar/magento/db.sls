# Drupal database specific information
# Shown with defaults
magento:
  # Database user drupal will use to connect to mysql
  db:
    user: magento
    password: magento
    host: "'%'"
    name: magento
    interface: eth0

  # Database user a replication slave will use to connect to mysql
  slave:
    user: magento_slave
    password: magento_slave
    host: "'%'"
