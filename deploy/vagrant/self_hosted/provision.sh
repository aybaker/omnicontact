#!/bin/bash

echo "Installing git and net-tools"
yum install git net-tools -y
cd /var/tmp/
git clone https://gitlab.com/omnileads/ominicontacto.git
cd ominicontacto
git fetch
git checkout $BRANCH
if [ "$MODE" == "AIO" ]; then
  python deploy/vagrant/edit_inventory.py --self_hosted=yes
  cd deploy/ansible
  ./deploy.sh -i --iface=eth1
elif [ "$MODE" == "DOCKER" ];then
    cd deploy/docker/prodenv
    sed -i "s/#DOCKER_HOSTNAME=your.hostname.com/DOCKER_HOSTNAME=$CENTOS_IP/g" .env
    sed -i "s/#DOCKER_IP=X.X.X.X/DOCKER_IP=$CENTOS_IP/g" .env
    sed -i "s/#RELEASE=release-1.3.4/RELEASE=$BRANCH/g" .env
    sed -i "s/#DJANGO_PASS=my_very_strong_pass/DJANGO_PASS=098098ZZZ/g" .env
    sed -i "s/#MYSQL_ROOT_PASS=my_very_strong_pass/MYSQL_ROOT_PASS=a/g" .env
    sed -i "s/#MYSQL_HOST=X.X.X.X/MYSQL_HOST=$CENTOS_IP/g" .env
    sed -i "s/#PGHOST=X.X.X.X/PGHOST=$CENTOS_IP/g" .env
    sed -i "s/#PGPASSWORD=my_very_strong_pass/PGPASSWORD=admin123/g" .env
    IS_CICD=true ./install.sh
fi
