# -*- coding: utf-8 -*-
# Copyright (C) 2018 Freetech Solutions

# This file is part of OMniLeads

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see http://www.gnu.org/licenses/.

import argparse
import os
import sys

parser = argparse.ArgumentParser(description='Modify Ansible inventory')

parser.add_argument("--remote_host", help="Sets external hostname to install OML on it")
parser.add_argument("--remote_ip_public", help="Sets external IP to install OML on it")
parser.add_argument("--remote_ip_internal", help="Sets internal IP in external server, "
                    "say 172.16.20.44")
parser.add_argument("--remote_port", help="Sets external ssh port to connect on remote server")
parser.add_argument("-dlu", "--docker_login_user", help="Username for docker hub")
parser.add_argument("-dle", "--docker_login_email", help="User email for docker hub")
parser.add_argument("-dlp", "--docker_login_password", help="User password for docker hub")
parser.add_argument("-tag", "--tag_docker_images", help="Specifies de tag for generated docker"
                    "images")
args = parser.parse_args()

# omininicontacto directorio raíz
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

inventory_path = os.path.join(base_dir, 'deploy/ansible/inventory')
inventory_file = open(inventory_path, 'r+')
inventory_contents = inventory_file.read()

if args.remote_host and args.remote_ip_public and args.remote_ip_internal:
    # modificamos el setting que define el servidor externo donde se va a instalar
    # el sistema
    if args.remote_port:
        remote_ssh_port = args.remote_port
    else:
        remote_ssh_port = 22
    inventory_file.seek(0)
    inventory_file.truncate()
    inventory_file.write(inventory_contents.replace(
        "#hostname ansible_ssh_port=22 ansible_user=root ansible_host=X.X.X.X"
        " #(this line is for node-host installation)",
        "{0} ansible_ssh_port={1} ansible_user=root ansible_host={2}".format(
            args.remote_host, remote_ssh_port, args.remote_ip_public)).replace(
                "#TZ=America/Argentina/Cordoba", "TZ=America/Argentina/Cordoba").replace(
                    "omni_ip=\"{{ ansible_host }}\"", "omni_ip={0}".format(
                        args.remote_ip_internal)))
    sys.exit()


if args.docker_login_user and args.docker_login_email and args.docker_login_password \
   and args.tag_docker_images:
    # editamos las líneas del inventory que indican que se va hacer un build
    # de imágenes de producción de los componentes del sistema
    # 1) modificando archivo con variables de ansible
    group_vars_path = os.path.join(base_dir, 'deploy/ansible/group_vars/docker_general_vars.yml')
    group_vars_file = open(group_vars_path, 'r+')
    group_vars_contents = group_vars_file.read()
    group_vars_file.seek(0)
    group_vars_file.truncate()
    group_vars_file.write(group_vars_contents.replace(
        "docker_login_user:", "docker_login_user: {0}".format(
            args.docker_login_user)).replace(
        "docker_login_email:", "docker_login_email: {0}".format(
            args.docker_login_email)).replace(
        "docker_login_pass:", "docker_login_pass: {0}".format(
            args.docker_login_password)))
    # 3) modificamos el archivo con las variables de docker prodenv
    prodenv_vars_path = os.path.join(base_dir, 'deploy/ansible/group_vars/docker_prodenv_vars.yml')
    prodenv_vars_file = open(prodenv_vars_path, 'r+')
    prodenv_vars_contents = prodenv_vars_file.read()
    prodenv_vars_file.seek(0)
    prodenv_vars_file.truncate()
    prodenv_vars_file.write(prodenv_vars_contents.replace("version:", "version: {0}".format(
        args.tag_docker_images), 1))

    # 2) modificando inventory
    inventory_contents = inventory_contents.replace(
        "[prodenv-container]\n#localhost ansible_connection=local",
        "[prodenv-container]\nlocalhost ansible_connection=local")
    inventory_contents = inventory_contents.replace(
        "#TZ=America/Argentina/Cordoba", "TZ=America/Argentina/Cordoba")
    inventory_contents = inventory_contents.replace(
        "docker_user='{{ lookup(\"env\",\"SUDO_USER\") }}'", "docker_user='root'")
    inventory_file.seek(0)
    inventory_file.truncate()
    inventory_file.write(inventory_contents)
    sys.exit()