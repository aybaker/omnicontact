#!/usr/bin/php -q
<?php
require ('phpagi.php') ;
//creando nueva instancia AGI
$agi = new AGI() ;
ob_implicit_flush(true) ;
set_time_limit(30) ;

$tipo_llamada=$argv[1];
$id_cliente=$argv[2];
$tel_cliente=$argv[3];
$grabacion=$argv[5];
$sip_agente=$argv[4];
$campana=$argv[6];
$fecha=$argv[7];
$uid=$argv[8];
$duracion=0;

$connection=pg_connect("host=127.0.0.1 port=5432 password=omnileadsrw user=omnileads")
or die('NO HAY CONEXION: ' . pg_last_error());

$query ="INSERT INTO ominicontacto_app_grabacion (fecha,tipo_llamada,id_cliente,tel_cliente,grabacion,sip_agente,campana_id,uid,duracion) VALUES ('$fecha','$tipo_llamada','$id_cliente','$tel_cliente','$grabacion','$sip_agente','$campana','$uid','$duracion');";

echo"$query\n";

$result=pg_query($connection, $query) or die('ERROR AL INSERTAR DATOS: ' . pg_last_error());

pg_close ($connection);
?>
