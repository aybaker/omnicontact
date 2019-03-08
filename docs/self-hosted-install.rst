Ansible Self-Hosted Install
^^^^^^^^^^^^^^^^^^^

- Cloning the official OML repository and select release to be deployed
::

 git clone https://gitlab.com/omnileads/ominicontacto.git
 cd ominicontacto
 git checkout master
|
where "master" is the OMniLeads stable release.

- Check your hostname and ip address
::

 hostname
 ip a
|

.. image:: images/hostname_command.png
        :align: center
        

.. image:: images/ip_a_command.png
        :align: center

- Edit your inventory file accord to the "hostname" and "ip a" commands output



.. image:: images/inventory_file_hostname_ip.png
        :align: center
