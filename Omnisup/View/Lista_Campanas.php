<?php
include_once $_SERVER['DOCUMENT_ROOT'] . '/Omnisup/config.php';
include_once controllers . '/Campana.php';
$SupervId = isset($_GET["supervId"]) ? $_GET["supervId"] : "";
$admin = isset($_GET['es_admin']) ? $_GET['es_admin'] : "";
if($SupervId) {
    $Controller_Campana = new Campana();
    if($admin && $admin == 't') {
        $resul = $Controller_Campana->traerCampanas();
    } else {
        $resul = $Controller_Campana->traerCampanas($SupervId);
    }
}
foreach ($resul as $clave => $valor) {
?>
<li>
    <a href="index.php?page=Detalle_Campana&nomcamp=<?= $valor ?>&supervId=<?= $SupervId ?>&es_admin=<?= $admin ?>&campId=<?= $clave ?>"><?= $valor ?></a>
</li>
<?php
}
?>
