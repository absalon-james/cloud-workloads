base:

  ############################
  ## Drupal ##################
  ############################
  'roles:drupal_mysql_master':
    - match: grain
    - drupal.db_master
  
  'roles:drupal_mysql_slave':
    - match: grain
    - drupal.db_slave

  'roles:drupal_web':
    - match: grain
    - drupal.web

  ############################
  ## Magento #################
  ############################
  'roles:magento_mysql_master':
    - match: grain
    - magento.db_master
  
  'roles:magento_mysql_slave':
    - match: grain
    - magento.db_slave

  'roles:magento_web':
    - match: grain
    - magento.web

  ############################
  ## DBT2 ####################
  ############################
  'roles:dbt2_db':
    - match: grain
    - dbt2.db

  'roles:dbt2':
    - match: grain
    - dbt2.dbt2
