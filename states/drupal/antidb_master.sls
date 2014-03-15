include:
  - mysql.antimysql

drupal_db_archive:
  file.absent:
    - name: /opt/drupal.db.tar.gz

drupal_db:
  file.absent:
    - name: /opt/drupal.db
