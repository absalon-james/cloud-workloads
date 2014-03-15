#!/bin/bash

# load_db_mysql.sh

usage() {

  if [ "$1" != "" ]; then
    echo ''
    echo "error: $1"
  fi

  echo ''
  echo 'usage: mysql_load_db.sh [options]'
  echo 'options:'
  echo 'Mandatory option:'
  echo '----------------'
  echo '       --path <path to dataset files> (mandatory unless only-create)'
  echo ''
  echo 'Configuration options:'
  echo '----------------------'
  echo '       --mysql-path <path to mysql client binary.'
  echo '         (default /usr/local/mysql/bin/mysql)>'
  echo '       --database <database name> (default dbt2)'
  echo '       --socket <database socket> (default /tmp/mysql.sock)'
  echo '       --host <database host> (default localhost)'
  echo '       --port <database port> (default 3306)'
  echo '       --user <database user> (default root)'
  echo '       --password <database password> (default not specified)'
  echo ''
  echo 'Partition options:'
  echo '------------------'
  echo '       --partition <use partitioning [NONE|KEY|HASH] (default NONE)>'
  echo '       --num-partitions <number of partitions to create in tables>'
  echo '         (default not specified)'
  echo ''
  echo 'MySQL Cluster Disk Data options:'
  echo '--------------------------------'
  echo '       --use-disk-cluster (if this is not set the other options in this'
  echo '         section will be ignored)'
  echo '       --logfile-group <Name of logfile group> (default lg1)'
  echo '       --tablespace <Name of tablespace> (default ts1)'
  echo '       --undofile <Name of undo log file> (default undofile.dat)'
  echo '       --datafile <Name of datafile in tablespace> (default datafile.dat)'
  echo '       --logfile-size <Size of undo log file> (default 256M)'
  echo '       --datafile-size <Size of datafile in tablespace> (default 12G)'
  echo ''
  echo 'Table options:'
  echo '--------------'
  echo '       --using-hash'
  echo '         (use hash index for primary keys, optimisation for NDB)'
  echo '       --engine <storage engine: [MYISAM|INNODB|BDB|NDB]. (default INNODB)>'
  echo ''
  echo 'Runtime options:'
  echo '----------------'
  echo '       --local <to use LOCAL keyword while loading dataset>'
  echo '       --parallel-load'
  echo '         (only load data, if data-files use different'
  echo '          warehouses parallel load is possible)'
  echo '       --only-create (Using this parameter means no tables will be loaded)'
  echo '       --only-item (Only create a MyISAM table and load it)'
  echo '       --item-use-myisam (Use MyISAM as storage engine for ITEM table)'
  echo '       --verbose'
  echo '       --help'
  echo ''
  echo 'Example: sh mysql_load_db.sh --path /tmp/dbt2-w3'
  echo ''
}


validate_parameter()
{
  if [ "$2" != "$3" ]; then
    usage "wrong argument '$2' for parameter '-$1'"
    exit 1
  fi
}


command_exec()
{
  if [ -n "$VERBOSE" ]; then
    echo "Executed command: $1"
  fi

  eval "$1 -p{{ salt['pillar.get']('db:password', 'dbt2') }}"

  rc=$?
  if [ $rc -ne 0 ]; then
   echo "ERROR: rc=$rc"
   case $rc in
     127) echo "COMMAND NOT FOUND"
          ;;
       *) echo "SCRIPT INTERRUPTED"
          ;;
    esac
    exit 255
  fi
}

load_tables()
{

if [ "$LOAD_TABLES" == "0" ]; then
  TABLES="item"
else
  TABLES="customer district history item new_order order_line orders stock warehouse"
fi

for TABLE in $TABLES ; do
  COLUMN_NAMES=
  if [ "$TABLE" = "history" ]; then
    COLUMN_NAMES="(h_c_id,h_c_d_id,h_c_w_id,h_d_id,h_w_id,h_date,h_amount,h_data)"
  fi
  if [ "$TABLE" != "item" -o "$DB_PARALLEL" != "1" -o "$LOAD_TABLES" == "0" ]; then
    echo "Loading table $TABLE"
    if [ "$TABLE" == "orders" ]; then
      FN="order"
    else
      FN="$TABLE"
    fi
    command_exec "$MYSQL $DB_NAME -e \"LOAD DATA $LOCAL INFILE \\\"$DB_PATH/$FN.data\\\" \
              INTO TABLE $TABLE FIELDS TERMINATED BY '\t' ${COLUMN_NAMES} \""
  fi
done
}

create_tables()
{

CUSTOMER="CREATE TABLE customer (
  c_id int(11) NOT NULL default '0',
  c_d_id int(11) NOT NULL default '0',
  c_w_id int(11) NOT NULL default '0',
  c_first varchar(16) default NULL,
  c_middle char(2) default NULL,
  c_last varchar(16) default NULL,
  c_street_1 varchar(20) default NULL,
  c_street_2 varchar(20) default NULL,
  c_city varchar(20) default NULL,
  c_state char(2) default NULL,
  c_zip varchar(9) default NULL,
  c_phone varchar(16) default NULL,
  c_since timestamp NOT NULL,
  c_credit char(2) default NULL,
  c_credit_lim decimal(24,12) default NULL,
  c_discount double default NULL,
  c_balance decimal(24,12) default NULL,
  c_ytd_payment decimal(24,12) default NULL,
  c_payment_cnt double default NULL,
  c_delivery_cnt double default NULL,
  c_data varchar(500),
  PRIMARY KEY $USING_HASH  (c_w_id,c_d_id,c_id),
  KEY c_w_id (c_w_id,c_d_id,c_last,c_first $EXTRA_CUST_INDEX_FIELDS)
)"

DISTRICT="CREATE TABLE district (
  d_id int(11) NOT NULL default '0',
  d_w_id int(11) NOT NULL default '0',
  d_name varchar(10) default NULL,
  d_street_1 varchar(20) default NULL,
  d_street_2 varchar(20) default NULL,
  d_city varchar(20) default NULL,
  d_state char(2) default NULL,
  d_zip varchar(9) default NULL,
  d_tax double default NULL,
  d_ytd decimal(24,12) default NULL,
  d_next_o_id int(11) default NULL,
  PRIMARY KEY $USING_HASH (d_w_id,d_id)
)"

HISTORY="CREATE TABLE history (
  h_id bigint(20) auto_increment,
  h_c_id int(11) default NULL,
  h_c_d_id int(11) default NULL,
  h_c_w_id int(11) default NULL,
  h_d_id int(11) default NULL,
  h_w_id int(11) default NULL,
  h_date timestamp NOT NULL,
  h_amount double default NULL,
  h_data varchar(24) default NULL,
  PRIMARY KEY $USING_HASH (h_id, h_w_id)
)"


ITEM="CREATE TABLE item (
  i_id int(11) NOT NULL default '0',
  i_im_id int(11) default NULL,
  i_name varchar(24) default NULL,
  i_price double default NULL,
  i_data varchar(50) default NULL,
  PRIMARY KEY $USING_HASH (i_id)
)"


NEW_ORDER="CREATE TABLE new_order (
  no_o_id int(11) NOT NULL default '0',
  no_d_id int(11) NOT NULL default '0',
  no_w_id int(11) NOT NULL default '0',
  PRIMARY KEY  (no_w_id,no_d_id,no_o_id)
)"

ORDER_LINE="CREATE TABLE order_line (
  ol_o_id int(11) NOT NULL default '0',
  ol_d_id int(11) NOT NULL default '0',
  ol_w_id int(11) NOT NULL default '0',
  ol_number int(11) NOT NULL default '0',
  ol_i_id int(11) default NULL,
  ol_supply_w_id int(11) default NULL,
  ol_delivery_d timestamp NOT NULL,
  ol_quantity double default NULL,
  ol_amount double default NULL,
  ol_dist_info varchar(24) default NULL,
  PRIMARY KEY  (ol_w_id,ol_d_id,ol_o_id,ol_number)
)"

ORDERS="CREATE TABLE orders (
  o_id int(11) NOT NULL default '0',
  o_d_id int(11) NOT NULL default '0',
  o_w_id int(11) NOT NULL default '0',
  o_c_id int(11) default NULL,
  o_entry_d timestamp NOT NULL,
  o_carrier_id int(11) default NULL,
  o_ol_cnt int(11) default NULL,
  o_all_local double default NULL,
  PRIMARY KEY $USING_HASH (o_w_id,o_d_id,o_id),
  KEY o_w_id (o_w_id,o_d_id,o_c_id,o_id)
)"


STOCK="CREATE TABLE stock (
  s_i_id int(11) NOT NULL default '0',
  s_w_id int(11) NOT NULL default '0',
  s_quantity double NOT NULL default '0',
  s_dist_01 varchar(24) default NULL,
  s_dist_02 varchar(24) default NULL,
  s_dist_03 varchar(24) default NULL,
  s_dist_04 varchar(24) default NULL,
  s_dist_05 varchar(24) default NULL,
  s_dist_06 varchar(24) default NULL,
  s_dist_07 varchar(24) default NULL,
  s_dist_08 varchar(24) default NULL,
  s_dist_09 varchar(24) default NULL,
  s_dist_10 varchar(24) default NULL,
  s_ytd decimal(16,8) default NULL,
  s_order_cnt double default NULL,
  s_remote_cnt double default NULL,
  s_data varchar(50) default NULL,
  PRIMARY KEY $USING_HASH (s_w_id,s_i_id),
  KEY  (s_w_id,s_i_id,s_quantity)
)"

WAREHOUSE="CREATE TABLE warehouse (
  w_id int(11) NOT NULL default '0',
  w_name varchar(10) default NULL,
  w_street_1 varchar(20) default NULL,
  w_street_2 varchar(20) default NULL,
  w_city varchar(20) default NULL,
  w_state char(2) default NULL,
  w_zip varchar(9) default NULL,
  w_tax double default NULL,
  w_ytd decimal(24,12) default NULL,
  PRIMARY KEY $USING_HASH (w_id)
)"

TABLES="STOCK ITEM ORDER_LINE ORDERS NEW_ORDER HISTORY CUSTOMER DISTRICT WAREHOUSE"
if [ "$DB_PARALLEL" != "1" ]; then
  for TABLE in $TABLES ; do

    if [ "$PARTITION" = "KEY" -o "$PARTITION" = "HASH" ]; then
      PARTITION_FIRST="PARTITION BY "
      PARTITION_FIRST="$PARTITION_FIRST $PARTITION"
      PARTITION_SYNTAX=""
      if [ "$TABLE" = "STOCK" ]; then
        PARTITION_SYNTAX="(s_w_id)"
      fi
      if [ "$TABLE" = "ORDERS" ]; then
        PARTITION_SYNTAX="(o_w_id)"
      fi
      if [ "$TABLE" = "ORDER_LINE" ]; then
        PARTITION_SYNTAX="(ol_w_id)"
      fi
      if [ "$TABLE" = "NEW_ORDER" ]; then
        PARTITION_SYNTAX="(no_w_id)"
      fi
      if [ "$TABLE" = "CUSTOMER" ]; then
        PARTITION_SYNTAX="(c_w_id)"
      fi
      if [ "$TABLE" = "WAREHOUSE" ]; then
        PARTITION_SYNTAX="(w_id)"
      fi
      if [ "$TABLE" = "DISTRICT" ]; then
        PARTITION_SYNTAX="(d_w_id)"
      fi
      if [ "$TABLE" = "HISTORY" ]; then
        PARTITION_SYNTAX="(h_w_id)"
      fi
      if [ "$PARTITION_SYNTAX" != "" ]; then
        PARTITION_SYNTAX="$PARTITION_FIRST $PARTITION_SYNTAX $PARTITION_NO"
      fi
    fi
    if [ "x$ONLY_ITEM" = "x" ] ; then
      if [ "$TABLE" = "HISTORY" -o "$TABLE" = "STOCK" -o "$TABLE" = "ORDERS" -o "$TABLE" = "ORDER_LINE" ]; then
        echo "Creating table $TABLE in $DB_ENGINE"
        command_exec "$MYSQL $DB_NAME -e \"\$$TABLE ENGINE=$DB_ENGINE $NDB_DISK_DATA $PARTITION_SYNTAX\""
      else
        if [ "x$TABLE" != "xITEM" ] ; then
          echo "Creating table $TABLE in $DB_ENGINE"
          command_exec "$MYSQL $DB_NAME -e \"\$$TABLE ENGINE=$DB_ENGINE $PARTITION_SYNTAX\""
        fi
      fi
    fi
    if [ "x$TABLE" = "xITEM" ] ; then
      if [ "x$USE_MYISAM_FOR_ITEM" = "x" ] ; then
        echo "Creating table $TABLE in $DB_ENGINE"
        command_exec "$MYSQL $DB_NAME -e \"\$$TABLE ENGINE=$DB_ENGINE $PARTITION_SYNTAX\""
      else
        echo "Creating table $TABLE in MYISAM"
        command_exec "$MYSQL $DB_NAME -e \"\$$TABLE ENGINE=MYISAM $PARTITION_SYNTAX\""
      fi
    fi
  done
fi

}

#DEFAULTs

LOAD_TABLES="1"
LOCAL=""
VERBOSE=""
DB_PASSWORD=""
DB_PATH=""
DB_NAME="dbt2"
DB_PARALLEL="0"

MYSQL="/usr/local/mysql/bin/mysql"
DB_HOST="localhost"
DB_PORT="3306"
DB_SOCKET=""
DB_USER="root"
DB_ENGINE="INNODB"
PARTITION_NO=""
PARTITION=""
NDB_DISK_DATA=""
USING_HASH=""
EXTRA_CUST_INDEX_FIELDS=""
LOGFILE_GROUP="lg1"
TABLESPACE="ts1"
LF_SIZE="256M"
TS_SIZE="12G"
UNDOFILE="'undofile.dat'"
DATAFILE="'datafile.dat'"
ONLY_ITEM=""
USE_MYISAM_FOR_ITEM=""

while test $# -gt 0
do
  case $1 in
  --only-item )
    ONLY_ITEM="1"
    ;;
  --item-use-myisam )
    USE_MYISAM_FOR_ITEM="1"
    ;;
  --tablespace | -tablespace | -ts | \
  --ts )
    shift
    TABLESPACE=$1
    ;;
  --logfile-group | logfile_group | -lf | \
  --lf )
    shift
    LOGFILE_GROUP=$1
    ;;
  --undofile | -undofile | -undo-file | --undo-file | \
  --undo_file | \
  -undo_file )
    shift
    UNDOFILE=$1
    ;;
  --datafile | -datafile | -data-file | --data-file | \
  --data_file | \
  -data_file )
    shift
    DATAFILE=$1
    ;;
  --logfile-size | --logfile_size | --log-file-size | -log-file-size | \
  --log_file_size | -log_file_size | --lf-size | -lf-size | --lf_size | \
  -lf_size )
    shift
    LF_SIZE=$1
    ;;
  --datafile-size | --datafile_size | --data-file-size | -data-file-size | \
  --data_file_size | -data_file_size | --d-size | -d-size | --d_size | \
  -d_size )
    shift
    TS_SIZE=$1
    ;;
  --partition | -partition )
    shift
    PARTITION=$1
    ;;
   --num_partitions | --num_partition | --num-partitions | \
   --num-partition | -num_partitions | -num_partition | \
   -num-partitions | \
   -num-partition )
     opt=$1
     shift
     PARTITION_NO=`echo $1 | egrep "^[0-9]+$"`
     validate_parameter $opt $1 $PARTITION_NO
     ;;
   --mysql-path | -mysql-path | -mysql | \
   --mysql_path | -mysql_path | \
   --mysql )
     shift
     MYSQL=$1
     ;;
   --database | --db | -database | \
   -db )
     shift
     DB_NAME=$1
     ;;
   --engine | -engine | --handler | -handler | --storage-engine | \
   --storage_engine | \
   -e )
     shift
      DB_ENGINE=$1
      ;;
    --path | -path | --data-file-path | -data-file-path | -datapath | \
    --data_file_path | -data_file_path | \
    -f )
      shift
      DB_PATH=$1
      ;;
    --use-disk-cluster | -use-disk-cluster | -ndb-disk | \
    -use_disk_cluster | ---use_disk_cluster | --ndb_disk | -ndb_disk | \
    --ndb-disk )
	NDB_DISK_DATA="1"
        EXTRA_CUST_INDEX_FIELDS=",c_discount,c_credit"
        ;;
    --host | -host | \
    -h )
      shift
      DB_HOST=$1
      ;;
    --using-hash | -using-hash | --using_hash | \
    -using_hash )
      USING_HASH="USING HASH"
      ;;
    --parallel-load | --parallel | --parallel_load | --parallel_load | \
    -parallel-load | -parallel | -parallel_load | -parallel_load | \
    --parallell-load | --parallell | --parallell_load | --parallell_load | \
    -parallell-load | -parallell | -parallell_load | -parallell_load | \
    --par )
      DB_PARALLEL="1"
      ;;
    --local | -local | \
    -l )
      LOCAL="LOCAL"
      ;;
    --only-create | --no-load | -only-create | -no-load | \
    --only_create | --no_load | -only_create | -no_load | \
    -o )
      LOAD_TABLES="0"
      ;;
    --password | --passwd | -password | \
    -passwd )
      shift
      DB_PASSWORD=$1
      ;;
    --socket | -socket | \
    -s )
      shift
      DB_SOCKET=$1
      ;;
    --port | -port | \
    -p )
      opt=$1
      shift
      DB_PORT=`echo $1 | egrep "^[0-9]+$"`
      validate_parameter $opt $1 $DB_PORT
      ;;
    --user | -user | \
    -u )
      shift
      DB_USER=$1
      ;;
    --verbose | -verbose | \
    -v )
      VERBOSE=1
      ;;
    --help | -help | \
    ? )
      usage
      exit 1
      ;;
    * )
      usage
      exit 1
      ;;
  esac
  shift
done

# Check parameters.
if [ "$LOAD_TABLES" == "1" ]; then
  if [ "$DB_PATH" == "" ]; then
    usage "specify path where dataset txt files are located - using -p #"
    exit 1
  fi

  if [ ! -d "$DB_PATH" ]; then
    usage "Directory '$DB_PATH' not exists. Please specify
         correct path to data files using --path #"
    exit 1
  fi
fi

if [ "$DB_HOST" != "localhost" ]; then
  DB_SOCKET=""
fi

if [ "$DB_ENGINE" != "INNODB" -a "$DB_ENGINE" != "MYISAM" -a "$DB_ENGINE" != "BDB" -a "$DB_ENGINE" != "NDB" ]; then
  usage "$DB_ENGINE. Please specifey correct storage engine [MYISAM|INNODB|BDB|NDB]"
  exit 1
fi

if [ "$PARTITION" != "" -a "$PARTITION" != "KEY" -a "$PARTITION" != "HASH" ]; then
  usage "PARTITION must be [KEY|HASH or not specified]"
  exit 1 
fi

if [ "$PARTITION_NO" != "" ]; then
  PARTITION_NO="PARTITIONS $PARTITION_NO"
fi
if [ ! -f "$MYSQL" ]; then
  usage "MySQL client binary '$MYSQL' not exists.
       Please specify correct one using -c #"
  exit 1
fi

if [ "$DB_PASSWORD" != "" ]; then
  MYSQL_ARGS="-p $DB_PASSWORD"
fi

MYSQL_ARGS="$MYSQL_ARGS -h $DB_HOST -u $DB_USER"
if [ "$DB_SOCKET" != "" ]; then
  MYSQL_ARGS="$MYSQL_ARGS --socket=$DB_SOCKET"
else
  MYSQL_ARGS="$MYSQL_ARGS --protocol=tcp"
fi
MYSQL_ARGS="$MYSQL_ARGS --port $DB_PORT"
MYSQL="$MYSQL $MYSQL_ARGS"

echo ""
echo "Loading of DBT2 dataset located in $DB_PATH to database $DB_NAME."
echo ""
echo "DB_ENGINE:      $DB_ENGINE"
echo "DB_HOST:        $DB_HOST"
echo "DB_PORT:        $DB_PORT"
echo "DB_USER:        $DB_USER"
echo "DB_SOCKET:      $DB_SOCKET"
echo "PARTITION:      $PARTITION"
echo "PARTITION_NO:   $PARTITION_NO"
echo "NDB_DISK_DATA:  $NDB_DISK_DATA"
echo "USING_HASH:     $USING_HASH"
echo "LOGFILE_GROUP:  $LOGFILE_GROUP"
echo "TABLESPACE:     $TABLESPACE"
echo "TABLESPACE SIZE: $TS_SIZE"
echo "LOGFILE SIZE:   $LF_SIZE"

if [ "$DB_PARALLEL" != "1" ]; then
  if [ "x$ONLY_ITEM" = "x" ]; then
    echo "DROP/CREATE Database"
    command_exec "$MYSQL -e \"drop database if exists $DB_NAME\" "
    command_exec "$MYSQL -e \"create database $DB_NAME\" "
    if [ "$NDB_DISK_DATA" != "" ]; then
      command_exec "$MYSQL -e \"create logfile group $LOGFILE_GROUP add undofile $UNDOFILE initial_size $LF_SIZE ENGINE=NDB\" "
      command_exec "$MYSQL -e \"create tablespace $TABLESPACE add datafile $DATAFILE use logfile group $LOGFILE_GROUP initial_size $TS_SIZE\" "
    fi
  fi
else
  echo "Running parallel load variant"
  command_exec "$MYSQL -e \"create database if not exists $DB_NAME\" "
fi

# Create tables
echo ""
create_tables

# Load tables
echo ""
load_tables
