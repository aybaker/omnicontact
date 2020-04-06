
$('#id_grupo').prop('disabled', true);
$('#id_rol').prop('disabled', true);
function tipo_usuario(){
        $('input[name="is_agente"]').click(function(){
            if($(this).prop("checked") == true){
                $('#id_grupo').prop('disabled', false);
            }
            else if($(this).prop("checked") == false){
                $('#id_grupo').prop('disabled', true);
            }
        });
        $('input[name="is_supervisor"]').click(function(){
            if($(this).prop("checked") == true){
                $('#id_rol').prop('disabled', false);
            }
            else if($(this).prop("checked") == false){
                $('#id_rol').prop('disabled', true);
            }
        });
    };

$(function(){
    tipo_usuario();
});