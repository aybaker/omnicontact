#!/bin/bash

cd $(dirname $0)

for x in $(cd ../fts_web ; ls -1 *.py | cut -d . -f 1 | sort) ; do
	F=fts_web_${x}.rst

cat > $F <<EOF

.. ARCHIVO AUTOGENERADO! Sera sobreescrito si se ejecuta ./gen.sh

fts_web.$x
====================================

.. automodule:: fts_web.$x
   :members:

EOF

done


for x in $(cd ../fts_daemon ; ls -1 *.py | cut -d . -f 1 | sort) ; do
	F=fts_daemon_${x}.rst

cat > $F <<EOF

.. ARCHIVO AUTOGENERADO! Sera sobreescrito si se ejecuta ./gen.sh

fts_daemon.$x
====================================

.. automodule:: fts_daemon.$x
   :members:

EOF

done

