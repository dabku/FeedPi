window.setInterval(function(){
    if($('#jpg_feed').get(0).complete){
        $('#jpg_feed').attr("src",jpg_feed_url+"?"+$.now());
    }
    },100);


window.setInterval(function(){
    if (document.getElementById("movement").checked == true) {
        if($('#jpg_thr_feed').get(0).complete){
            $('#jpg_thr_feed').attr("src",jpg_thr_feed_url+"?"+$.now());
        }
        }
    },100);


$(document).ready(function() {
$("input[type='checkbox']#movement").change( function(e) {
    if (document.getElementById("movement").checked == true){
            $("#jpg_thr_feed").show();

    }else{
    $("#jpg_thr_feed").hide();
    };
});
});