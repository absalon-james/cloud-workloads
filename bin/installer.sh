#!/bin/bash

_SUCCESS=0

# Install salt master and salt minion
echo "Bootstrapping salt-master and salt-minion..."
curl -L http://bootstrap.saltstack.org | sudo sh -s -- -M
RETCODE=$?
if [ $RETCODE -ne $_SUCCESS ] ; then
    exit $RETCODE
fi

# Download salt state and pillar files
FILENAME="salt_states_and_pillars.tar.gz"
cd /srv
echo "Downloading salt states and pillars..."
sudo wget -O $FILENAME http://91130b1325445faefa46-0a57a58cc8418ee081f89836dd343dea.r74.cf1.rackcdn.com/cloud_workloads_states_pillars.tar.gz
RETCODE=$?
if [ $RETCODE -ne $_SUCCESS ] ; then
    exit $RETCODE
fi

# Uncompress downloaded files
echo "Uncompressing salt states and pillars..."
sudo tar -zxf $FILENAME
RETCODE=$?
if [ $RETCODE -ne $_SUCCESS ] ; then
    exit $RETCODE
fi

# Remove archive
sudo rm $FILENAME

# Apply local state to local machine to install other software and configure the master
sudo salt-call --local state.sls local 
RETCODE=$?
if [ $RETCODE -ne $_SUCCESS ] ; then
    exit $RETCODE
fi

# Configure cloud-workloads
echo "Configuring cloud-workloads..."
sudo cloud-workloads-configure
RETCODE=$?
if [ $RETCODE -ne $_SUCCESS ] ; then
    exit $RETCODE
fi

# Test the minion connectivity with the minion installer
sudo cloud-workloads-minion-installer -test
RETCODE=$?
if [ $RETCODE -ne $_SUCCESS ] ; then
    exit $RETCODE
fi

# Install salt-minion on minions in /etc/salt/roster
echo "Installing salt-minion on minions..."
sudo cloud-workloads-minion-installer
RETCODE=$?
if [ $RETCODE -ne $_SUCCESS ] ; then
    exit $RETCODE
fi

# Sleep a few seconds, wait for the minions to come online
sleep 15

# Run cloud-workloads with the sample yaml config
echo "Running cloud-workloads..."
sudo cloud-workloads-runner /etc/cloud_workloads/sample.yaml cloud_workloads
RETCODE=$?
if [ $RETCODE -ne $_SUCCESS ] ; then
    exit $RETCODE
fi
