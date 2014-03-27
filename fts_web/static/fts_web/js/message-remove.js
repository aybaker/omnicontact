$(function(){
    message_remove(function(){});
    
    function message_remove(callback){
        window.setTimeout(function() {
            $(".alert-dismissable").fadeTo(500, 0).slideUp(500, function(){
                $(this).remove(); 
                callback();
            });
        }, 8000);
    }
});