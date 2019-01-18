//update gallery on first load
$(document).ready(function(){
    update_gallery();
     return false;
});

$(document).ready(function(){
    $('button#reload_images').bind('click', function()
    {
        $('#div_photos').empty();
        update_gallery();
        return false;
    });
});

function update_gallery(){
$.getJSON($SCRIPT_ROOT + '/_get_images', {}, function(data) {

        $('#div_photos').empty();
        $.each(data.result.still_imgs, function(i,image)
        {
         $("#div_photos").append("<a href=\""+
         data.dir+image+
         "\"data-lightbox=\"gallery\"><img class=\"photos\" data-lightbox=\"gallery\" src=\""+
         data.dir+image+
         "\"></a>");

        });
     });
     $("#div_photos").fadeIn("slow");
}