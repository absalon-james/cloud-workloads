#!/bin/bash

usage() {
  echo ''
  echo 'usage: mysql_load_sp.sh [options]'
  echo 'options:'
  echo '--database             <database name (default dbt2)>'
  echo '--client-path          <path to mysql client binary (default /usr/local/mysql/bin)>'
  echo '--sp-path              <path to Stored Procedures (default ../../stored_procedures/mysql)>'
  echo '--host                 <database host (default localhost)>'
  echo '--port                 <database port (default 3306)>'
  echo '--socket               <database socket (default use tcp protocol)>'
  echo '--user                 <Database user (default root)>'
  echo '--password             <Database password (default no password)>'
  echo ''
  echo 'Example: sh mysql_load_sp.sh --database dbt2'
  echo ''

  if [ "$1" != "" ]; then
    echo ''
    echo "error: $1"
  fi
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

load_sp()
{
  PROCEDURES="delivery new_order new_order_2 order_status payment stock_level"

  for PROCEDURE in $PROCEDURES ; do

  echo "Load SP: $PROCEDURE"
  command_exec "$MYSQL < $PATH_SP/$PROCEDURE.sql"

  done
}

#DEFAULTs

VERBOSE=""
DB_PASSWORD=""
DB_NAME="dbt2"
MYSQL="/usr/local/mysql/bin/mysql"
DB_HOST="localhost"
DB_SOCKET="--protocol=tcp"
DB_USER="root"
DB_PORT="3306"
PATH_SP="../../storedproc/mysql"

while test $# -gt 0
do
  case $1 in
    --database | -database)
      shift
      DB_NAME=$1
      ;;
    --sp-path | --sp_path | -sp-path | -sp_path )
      shift
      PATH_SP=$1
      ;;
    --client-path | --client_path | -client-path | -client_path )
      shift
      MYSQL="$1/mysql"
      ;;
    --host | -host )
      shift
      DB_HOST=$1
      ;;
    --port | -port )
      opt=$1
      shift
      DB_PORT=`echo $1 | egrep "^[0-9]+$"`
      validate_parameter $opt $1 $DB_PORT
      ;;
    --user | -user )
      shift
      DB_USER=$1
      ;;
    --password | -password )
      shift
      DB_PASSWORD=$1
      ;;
    --socket | -socket )
      shift
      DB_SOCKET="--socket=$1"
      ;;
    --help | -help | -h | ? | -? )
      usage
      exit 0
      ;;
    * )
      usage "$1 not found"
      exit 1
      ;;
  esac
  shift
done

if [ ! -d "$PATH_SP" ]; then 
  usage "Directory '$PATH_SP' not exists. Please specify 
       correct path to SPs using --sp-path #"
  exit 1
fi

if [ ! -f "$MYSQL" ]; then
  usage "MySQL client binary '$MYSQL' doesn't exist. 
       Please specify correct one using --client-path #"
  exit 1
fi

MYSQL_VER=`$MYSQL --version | sed -e "s/.* \([0-9]*\).*,.*/\1/"`

if [ $MYSQL_VER -lt 5 ]; then
  usage "In order to load stored procedures you have to use mysql client binary from MySQL 
       distribution 5.0 or higher. Please specify correct binary using --client-path #"
  exit 1
fi

if [ "x$DB_PASSWORD" != "x" ]; then
  MYSQL_ARGS="-p $DB_PASSWORD"
fi

MYSQL_ARGS="$MYSQL_ARGS -h $DB_HOST -u $DB_USER --port $DB_PORT $DB_SOCKET"
MYSQL="$MYSQL $MYSQL_ARGS"

command_exec "$MYSQL -e \"create database if not exists $DB_NAME\" "

MYSQL="$MYSQL --database $DB_NAME"

echo ""
echo "Loading of DBT2 SPs located in $PATH_SP to database $DB_NAME."
echo ""
echo "Start by creating database if it not already exists"

load_sp
