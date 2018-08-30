#!/bin/bash

BD="${BD:-omnileads}"

while [ -n "$1" ] ; do
	# Nombre de stored proc. es igual al nombre del archivo
	proc_name="$(basename $1 .sql)"
	echo "Procesando procedimiento almacenado $proc_name"

	existe=$(sudo -u postgres psql -tAq -c "select count(*) from pg_proc where proname = '$proc_name'" $BD)

	if [ "$existe" -eq "1" ] ; then
		echo " - El procedimiento ya existen en BD"
	else
		echo " - Creando procedimiento..."
		sudo -u postgres psql -f - $BD < $1
		EXIT_STATUS=$?
		if [ "$EXIT_STATUS" -ne "0" ] ; then
			echo "ERROR: exit status de psql: $EXIT_STATUS"
			exit $EXIT_STATUS
		fi	
	fi

	# Continuamos con siguiente
	shift
done
