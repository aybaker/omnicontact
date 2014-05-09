#!/bin/bash

cd $(dirname $0)

for x in $(cd ../fts_web ; ls -1 *.py | cut -d . -f 1 | grep -v sample_settings_local | grep -v __init__ | sort) ; do
	F=fts_web_${x}.rst

cat > $F <<EOF

.. ARCHIVO AUTOGENERADO! Sera sobreescrito si se ejecuta ./gen.sh

fts_web.$x
====================================

.. automodule:: fts_web.$x
   :members:

EOF

done


for x in $(cd ../fts_daemon ; ls -1 *.py | cut -d . -f 1 | grep -v __init__ | grep -v poll_daemon | sort) ; do
	F=fts_daemon_${x}.rst

cat > $F <<EOF

.. ARCHIVO AUTOGENERADO! Sera sobreescrito si se ejecuta ./gen.sh

fts_daemon.$x
====================================

.. automodule:: fts_daemon.$x
   :members:

EOF

done

for x in $(cd ../fts_daemon/poll_daemon ; ls -1 *.py | cut -d . -f 1 | grep -v __init__ | grep -v main | sort) ; do
	F=fts_daemon_poll_daemon_${x}.rst

cat > $F <<EOF

.. ARCHIVO AUTOGENERADO! Sera sobreescrito si se ejecuta ./gen.sh

fts_daemon.poll_daemon.$x
====================================

.. automodule:: fts_daemon.poll_daemon.$x
   :members:

EOF

done

