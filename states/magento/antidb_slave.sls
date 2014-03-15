{% from "magento/db.jinja" import magento with context %}
include:
  - mysql.antimysql

{% if magento.master %}
/opt/magento.db:
  file.absent:
    - name: /opt/magento.db
{% endif %}
