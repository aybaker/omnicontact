#!/bin/bash

#
# Shell script para facilitar el deploy de la aplicación desde un servidor de deploy
#
# Autor: Andres Felipe Macias
# Colaborador:  Federico Peker
#
ANSIBLE=`which ansible`
PIP=`which pip`
current_directory=`pwd`
export ANSIBLE_CONFIG=$current_directory

Help() {
USAGE="
       Deploy de FTS-ICS
       Opciones a ingresar: \n
            -h: ayuda \n
            -r: rama a deployar (ej: -r develop) \n
            -i: instala ansible, transfiere llaves ssh a maquina a deployar, ingresar fqdn, formato de grabaciones, pass de OML \n
            -t: ingresar ip, opcion de SO, tags de ansible (TAREAS A EJECUTAR y no ejecutar) \n
       EJEMPLOS: \n
       - ./deploy.sh -r develop -t all -> deployará la rama develop, ejecutara todas las tareas \n
       - ./deploy.sh -r release-0.4 -i -t kamailio,nginx,kamailio-cert -> deploya la rama release-0.4, pide datos del server, ejecuta las tareas de instalación de kamailio y de nginx  exceptuando la creacion de certificados (tiene que estar separado por coma) \n
       - ./deploy.sh -r release-0.4 -i -t asterisk,,kamailio-cert -> igual al anterior, solamente ejecutará tareas de instalación de asterisk exceptuando la creacion de certificados \n
       \n "
       echo -e $USAGE
       exit 1
}

Rama() {
    cd $current_directory
    echo "Creando directorio temporal de ansible"
    mkdir -p /var/tmp/ansible-ics
    TMP_ANSIBLE='/var/tmp/ansible-ics'
    echo "Copiando el contenido de ansible del repositorio al directorio temporal"
    cp -a $current_directory/* $TMP_ANSIBLE
    cd ..
    echo "Pasando al deploy de OmniAPP"
    set -e
    echo ""
    echo "Se iniciará deploy:"
    echo ""
    echo "      Version: $1"
    #echo "   Inventario: $INVENTORY"
    echo ""

    cd ~/ftsenderweb
    git checkout $1
    git pull origin +$1:$1

    ################### Build.sh #####################

    #set -e
    #cd $(dirname $0)
    TMP=/var/tmp/ftsender-build
    if [ -e $TMP ] ; then
        rm -rf $TMP
    fi
    mkdir -p $TMP/app
    echo "Usando directorio temporal: $TMP/ftsender..."
    echo "Creando bundle usando git-archive..."
    git archive --format=tar $(git rev-parse HEAD) | tar x -f - -C $TMP/app

    echo "Eliminando archivos innecesarios..."
    rm -rf $TMP/app/fts_tests
    rm -rf $TMP/app/docs
    rm -rf $TMP/app/deploy
    rm -rf $TMP/app/build
    rm -rf $TMP/app/run_coverage*
    rm -rf $TMP/app/run_sphinx.sh

    mkdir -p $TMP/appsms
    echo "Usando directorio temporal: $TMP/appsms..."

    mkdir -p $TMP/apidinstar
    echo "Usando directorio temporal: $TMP/apidinstar..."

    echo "Descargando api dinstar en directorio temporal"
    tar -xzf ~/ftsenderweb/aplicacionsms/dinstar.tar.gz -C $TMP/apidinstar

    echo "Obteniendo datos de version..."
    branch_name=$(git symbolic-ref -q HEAD)
    branch_name=${branch_name##refs/heads/}
    branch_name=${branch_name:-HEAD}

    commit="$(git rev-parse HEAD)"
    author="$(id -un)@$(hostname)"

    echo "Creando archivo de version | Branch: $branch_name | Commit: $commit | Autor: $author"
    cat > $TMP/app/fts_web/version.py <<EOF

#
# Archivo autogenerado
#

FTSENDER_BRANCH="${branch_name}"
FTSENDER_COMMIT="${commit}"
FTSENDER_BUILD_DATE="$(env LC_ALL=C LC_TIME=C date)"
FTSENDER_AUTHOR="${author}"

if __name__ == '__main__':
    print FTSENDER_COMMIT

EOF

    echo "Validando version.py - Commit:"
    python $TMP/app/fts_web/version.py

    # ----------
    export DO_CHECKS="${DO_CHECKS:-no}"
}

Preliminar() {

    echo "Bienvenido al asistente de instalación de ICS"
    echo ""
    echo "Instalando ansible 2.4.0"

    if [ -z $ANSIBLE ]; then
        $PIP install 'ansible==2.4.0.0'
    else
        echo "Ya tiene instalado ansible"
    fi

    if [ -f ~/.ssh/id_rsa.pub ]; then
        echo "Ya se han generado llaves para este usuario"
    else
        echo "Generando llaves públicas de usuario actual"
        ssh-keygen
    fi

}

#IngresarIP(){
#}

Tag() {

    echo -en "Ingrese IP  de maquina a deployar: "; read ip
    sed -i "21s/.*/$ip ansible_ssh_port=22/" $TMP_ANSIBLE/hosts
    echo "Transifiendo llave publica a usuario ftsender de Centos"
    ssh-copy-id -i ~/.ssh/id_rsa.pub ftsender@$ip
    ansible-playbook -s $TMP_ANSIBLE/playbook.yml --extra-vars "BUILD_DIR=$TMP/app BUILD_DIR_SMS=$TMP/appsms BUILD_API_DINSTAR=$TMP/apidinstar" --tags "${array[0]},${array[1]}" --skip-tags "${array[2]}" -K
    ResultadoAnsible=`echo $?`

if [ ${ResultadoAnsible} -ne 0 ];then
    echo "Falló la ejecucion de Ansible, favor volver a correr el script"
    exit 0
fi
#else

#if [ $opcion -eq 1 ]; then
#    echo "Ejecutando Ansible en Debian omni-app"
#    ansible-playbook -s /etc/ansible/deploy/omni-app-debian.yml -u freetech --extra-vars "BUILD_DIR=$TMP/ominicontacto" -K
#    echo "Ejecutando Ansible para copia de archivos entre servers"
#    ansible-playbook -s /etc/ansible/deploy/omniapp_second/transfer.yml -u root -K
#    echo "Finalizó la instalación de Omnileads"

}

while getopts "r::t:ih" OPTION;do
	case "${OPTION}" in
		r) # Rama a deployar
            Rama $OPTARG
		;;
		i) #Realizar pasos y agregar opciones preliminares
		    Preliminar
		   # IngresarIP
		;;
		t) #Tag
		    set -f # disable glob
            IFS=',' # split on space characters
            array=($OPTARG) # use the split+glob operator
   		    Tag $array
		;;
		h) # Print the help option
			Help
		;;

	esac
done
if [ $# -eq 0  ]; then Help; fi

