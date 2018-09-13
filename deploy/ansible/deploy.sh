#!/bin/bash

#
# Shell script para facilitar el deploy de la aplicación desde un servidor de deploy
#
# Autor: Andres Felipe Macias
# Colaborador:  Federico Peker
#
# Que hace este shell script?
# 1. Instala ansible
# 2. Copia toda la carpeta ansible del repo a /var/tmp/ansible y todo el codigo a /var/tmp/ominicontacto-build
# 3. Pregunta si se quiere dockerizar asterisk o no, para pasarle la variable a ansible.
# 4. Ejecuta ansible segun la opcion de Dockerizar o no
DOCKER="false"
PIP=`which pip`
current_directory=`pwd`
TMP_ANSIBLE='/var/tmp/ansible'
export ANSIBLE_CONFIG=$TMP_ANSIBLE
IS_ANSIBLE="`find /usr/bin /usr/sbin /usr/local /root ~ -name ansible 2>/dev/null |grep \"/bin/ansible\" |head -1`"

Help() {
USAGE="
       Opciones a ingresar: \n
            -h: ayuda \n
            -r: rama a deployar (ej: -r develop) \n
            -i: instala ansible, ingresar formato de grabaciones, pass de OML \n
            -t: ingresar ip, opcion de SO, tags de ansible (TAREAS A EJECUTAR) \n
        \n
       EJEMPLOS: \n
       - ./deploy.sh -r develop -t all -> deployará la rama develop, ejecutara todas las tareas \n
       \n
       Tags disponibles: \n
       all: ejecuta todos los procesos \n
       postinstall: ejecuta tareas necesarias para un post-deploy \n "
       echo -e $USAGE
       exit 1
}

Rama() {

    echo ""
    echo "###############################################################"
    echo "##    Bienvenido al asistente de instalación de Omnileads    ##"
    echo "###############################################################"
    echo ""
    sleep 2
    echo "Detectando si ansible 2.5.0 se encuentra instalado"
    if [ -z "$IS_ANSIBLE" ] ; then
        echo "No tienes instalado ansible"
        echo "Instalando ansible 2.5.0"
	    echo ""
	    $PIP install 'ansible==2.5.0.0' --user
        IS_ANSIBLE="`find /usr/bin /usr/sbin /usr/local /root ~ -name ansible |grep \"/bin/ansible\" |head -1 2> /dev/null`"
	fi
    ANS_VERSION=`"$IS_ANSIBLE" --version |grep ansible |head -1`
	if [ "$ANS_VERSION" = 'ansible 2.5.0' ] ; then
         echo "Ansible ya se encuentra instalado"
    else
        echo "Tienes una versión de ansible distinta a la 2.5.0"
        echo "Instalando versión 2.5.0"
        $PIP install 'ansible==2.5.0.0' --user
    fi

    cd $current_directory
    USUARIO="`grep ansible_user hosts| head -1 |awk -F " " '{print $3}'|awk -F "=" '{print $2}'`"
    sleep 2
    echo "Creando directorio temporal de ansible"
    if [ -e $TMP_ANSIBLE ]; then
        rm -rf $TMP_ANSIBLE
    fi
    mkdir -p /var/tmp/ansible
    sleep 2
    echo "Copiando el contenido de ansible del repositorio al directorio temporal"
    cp -a $current_directory/* $TMP_ANSIBLE

    if [ -z $FROM_INTWO ]; then
        echo ""
    else
        sed -i "s/\(^LOCALHOST\).*/LOCALHOST=true/" $TMP_ANSIBLE/hosts
    fi

    sleep 2
    echo "Creando directorio y carpeta de logs de proceso de instalación"
    mkdir -p /var/tmp/log
    touch /var/tmp/log/oml_install
    #sleep 2
    cd ../..
    echo "Chequeando y copiando el código a deployar"
    set -e
    echo ""
    echo "Se iniciará deploy:"
    echo ""
    echo "      Version: $1"
    echo ""

    git checkout deploy/ansible/hosts
    git checkout $1 1> /dev/null

    TMP=/var/tmp/ominicontacto-build
    if [ -e $TMP ] ; then
        rm -rf $TMP
    fi
    mkdir -p $TMP/ominicontacto
    echo "Usando directorio temporal: $TMP/ominicontacto..."
    sleep 2
    echo "Copiando el código al directorio temporal "
    git archive --format=tar $(git rev-parse HEAD) | tar x -f - -C $TMP/ominicontacto
    sleep 2
    echo "Eliminando archivos innecesarios..."
    rm -rf $TMP/ominicontacto/docs
    rm -rf $TMP/ominicontacto/ansible
    rm -rf $TMP/ominicontacto/run_coverage_tests.sh
    rm -rf $TMP/ominicontacto/oml_settings_local_1_host_pro.py
    rm -rf $TMP/ominicontacto/oml_settings_local_pro.py
    rm -rf $TMP/ominicontacto/test*
    sleep 2
    echo "Obteniendo datos de version..."
    branch_name=$(git symbolic-ref -q HEAD)
    branch_name=${branch_name##refs/heads/}
    branch_name=${branch_name:-HEAD}

    commit="$(git rev-parse HEAD)"
    author="$(id -un)@$(hostname)"

    echo -e "Creando archivo de version
       Branch: $branch_name
       Commit: $commit
       Autor: $author"
    cat > $TMP/ominicontacto/ominicontacto_app/version.py <<EOF

#
# Archivo autogenerado
#

OML_BRANCH="${branch_name}"
OML_COMMIT="${commit}"
OML_BUILD_DATE="$(env LC_hosts=C LC_TIME=C date)"
OML_AUTHOR="${author}"

if __name__ == '__main__':
    print OML_COMMIT


EOF

    #echo "Validando version.py - Commit:"
    python $TMP/ominicontacto/ominicontacto_app/version.py > /dev/null 2>&1

    # ----------
    export DO_CHECKS="${DO_CHECKS:-no}"
    rama=$1
}

Docker(){
#    while true; do
#      echo -en "Desea correr asterisk en container (no recomendado para producción)? [si/no]: "; read pregunta
#      if [ $pregunta == "si" ] || [ $pregunta == "Si" ]; then
#        DOCKER="true"
#        sed -i "s/\(^DOCKER\).*/DOCKER=true/" $TMP_ANSIBLE/hosts
#        break
#      elif [ $pregunta == "no" ] || [ $pregunta == "No" ]; then
#        sed -i "s/\(^DOCKER\).*/DOCKER=false/" $TMP_ANSIBLE/hosts
#        DOCKER="false"
#        break
#      else
#        echo "Opción inválida ingrese si o no"
#      fi
#    done
echo ""
}

Preliminar() {
    Docker
}

Desarrollo() {
    echo ""
    echo "#############################################################################"
    echo "Escogió la opción -d por lo que el deploy es para una máquina de desarrollo"
    echo "#############################################################################"
    echo ""
    sed -i "s/\(^desarrollo\).*/desarrollo=1/" $TMP_ANSIBLE/hosts
}

Tag() {

    echo "Comenzando la instalación de Omnileads con Ansible, este proceso puede tardar varios minutos"
    echo ""
    echo "Si comes bien hoy, tu cuerpo lo agradecerá mañana"
    echo "El servicio sin humildad es egoísmo"
    echo "Reflexionar serena, muy serenamente, es mejor que tomar decisiones desesperadas - Franz Kafka"
    echo ""
    if [ $DOCKER == "true" ]; then
      ${IS_ANSIBLE}-playbook -s $TMP_ANSIBLE/docker.yml --extra-vars "BUILD_DIR=$TMP/ominicontacto RAMA=$rama" --tags "${array[0]},${array[1]}" --skip-tags "${array[2]}" -K
    else
      ${IS_ANSIBLE}-playbook -s $TMP_ANSIBLE/omnileads.yml --extra-vars "BUILD_DIR=$TMP/ominicontacto RAMA=$rama" --tags "${array[0]},${array[1]}" --skip-tags "${array[2]}" -K

    fi
    ResultadoAnsible=`echo $?`
    echo "Finalizó la instalación Omnileads"
    echo ""

if [ ${ResultadoAnsible} -ne 0 ];then
    echo "Falló la ejecucion de Ansible, favor volver a correr el script"
    exit 0
fi

echo "Eliminando carpetas temporales creadas por este script"
rm -rf /var/tmp/ansible
rm -rf /var/tmp/ominicontacto-build

}

while getopts "r::t:ihd" OPTION;do
	case "${OPTION}" in
		r) # Rama a deployar
            Rama $OPTARG
		;;
		i) #Realizar pasos y agregar opciones preliminares
		    Preliminar
		;;
    d) #Cliente de desarrollo?
		    Desarrollo
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
