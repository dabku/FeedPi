$(document).ready(function(){
    update_settings()
    $('button#get_config').bind('click', function() {
        update_settings();
        });
 return false;
});

function update_settings() {
        $.getJSON($SCRIPT_ROOT + '/_get_settings', {}, function(data) {
            $('#text_loop_delay').val(data.settings.general.loop_delay);
            $('#check_enable_overlay').prop('checked',data.settings.general.overlay);
            $('#text_feed_resolution_x').val(data.settings.general.feed_res[0]);
            $('#text_feed_resolution_y').val(data.settings.general.feed_res[1]);

            $('#text_threshold').val(data.settings.vision.frame_threshold);
            $('#text_movement_threshold').val(data.settings.vision.movement_threshold);
            $('#text_movement_cooldown').val(data.settings.vision.movement_cooldown);
            $('#check_noise_pass').prop('checked',data.settings.vision.noise_pass);
            $('#text_mov_resolution_x').val(data.settings.vision.camera.movement_res[0]);
            $('#text_mov_resolution_y').val(data.settings.vision.camera.movement_res[1]);

            $('#text_iso').val(data.settings.vision.camera.iso);
            $('#text_brightness').val(data.settings.vision.camera.brightness);
            $('#text_contrast').val(data.settings.vision.camera.contrast);
            $('#text_framerate').val(data.settings.vision.camera.fps);
            $('#text_exposure').val(data.settings.vision.camera.exposure);

            $('#text_resolution_x').val(data.settings.vision.camera.camera_res[0]);
            $('#text_resolution_y').val(data.settings.vision.camera.camera_res[1]);

            $('#check_save_image').prop('checked',data.settings.general.save_images);
            $('#text_image_cooldown').val(data.settings.vision.image_saving_cooldown);
            $('#text_image_dir').val(data.settings.general.images_dir);

            $('#check_save_video').prop('checked',data.settings.general.save_videos);
            $('#text_video_cooldown').val(data.settings.vision.video_saving_cooldown);
            $('#text_videos_dir').val(data.settings.general.videos_dir);

            $('#check_discord_enabled').prop('checked',data.settings.discord.enabled);
            $('#check_discord_on_demand').prop('checked',data.settings.discord.on_demand);
            $('#check_discord_triggering').prop('checked',data.settings.discord.triggering);
            $('#discord_cooldown').val(data.settings.discord.videos_dir);
            $('#discord_address').val(data.settings.discord.comm_port);
            $('#discord_port').val(data.settings.discord.server_address);
         });
};

$(document).ready(function(){
        $('button#apply_config').bind('click', function() {
            json=JSON.stringify({
            general:{
                loop_delay:$('#text_loop_delay').val(),
                overlay:$('#check_enable_overlay').prop('checked'),
                feed_res:[$('#text_feed_resolution_x').val(), $('#text_feed_resolution_y').val()],
                images_dir:$('#text_image_dir').val(),
                save_images:$('#check_save_image').prop('checked'),
                save_videos:$('#check_save_video').prop('checked'),
                videos_dir:$('#text_videos_dir').val()
            },
            vision:{
                camera:{
                    iso:$('#text_iso').val(),
                    brightness:$('#text_brightness').val(),
                    contrast:$('#text_contrast').val(),
                    fps:$('#text_framerate').val(),
                    shutter_speed:$('#text_shutter_speed').val(),
                    camera_res:[$('#text_resolution_x').val(), $('#text_resolution_y').val()],
                    movement_res:[$('#text_mov_resolution_x').val(), $('#text_mov_resolution_y').val()]
                },
                movement_threshold: $('#text_movement_threshold').val(),
                frame_threshold:$('#text_threshold').val(),
                movement_cooldown:$('#text_movement_cooldown').val(),
                movement_low_pass:$('#check_low_pass').prop('checked'),
                noise_pass:$('#check_noise_pass').prop('checked'),
                threshold:$('#text_threshold').val(),
                image_saving_cooldown:$('#text_image_cooldown').val(),
                video_saving_cooldown:$('#text_video_cooldown').val()
            },
            discord:{
                cooldown:$('#discord_cooldown').val(),
                enabled:$('#check_discord_enabled').prop('checked'),
                on_demand:$('#check_discord_on_demand').prop('checked'),
                triggering:$('#check_discord_triggering').prop('checked')
            }
           });
            $.ajax({
                type:"POST",
                url:$SCRIPT_ROOT + '/_save_settings',
                contentType: "application/json",
                dataType:'json',
                data:json,
                success: function(data)
                {
                    alert(data.result);
                }
            });

        });
    });

$(document).ready(function(){

    $('button#write_file').bind('click', function() {

        $.ajax({
            type:"POST",
            url:$SCRIPT_ROOT + '/_save_settings_file'
        });
    return false;
});
});

$(document).ready(function(){
    $('button#restore_file').bind('click', function() {
        $.ajax({
            type:"POST",
            url:$SCRIPT_ROOT + '/_load_settings_file'
        });
 return false;
    });
});



$(document).ready(function(){

    $('button#apply_config').bind('click', function() {
        json=JSON.stringify({iso:$('#text_iso').val(),
        brightness:$('#text_brightness').val(),
        contrast:$('#text_contrast').val(),
        fps:$('#text_framerate').val()});
        $.ajax({
            type:"POST",
            url:$SCRIPT_ROOT + '/_save_pi_settings',
            contentType: "application/json",
            dataType:'json',
            data:json,
            success: function(data)
            {
                alert(data.result);
            }
        });
    });
});
$(document).ready(function(){
    $('button#read_piconf').bind('click', function() {
        $.getJSON($SCRIPT_ROOT + '/_get_pi_settings', {}, function(data) {
            console.log(data.settings);
            $('#text_iso').val(data.settings.iso);
            $('#text_brightness').val(data.settings.brightness);
            $('#text_contrast').val(data.settings.contrast);
            $('#text_framerate').val(data.settings.fps);
         });
 return false;
    });
});