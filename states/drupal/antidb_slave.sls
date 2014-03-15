include:
  - mysql.antimysql

drupal_db:
  file.absent:
    - name: /opt/drupal.db
