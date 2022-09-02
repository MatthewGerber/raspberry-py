$(function () {
    $('#led-1').on('change', function () {
        $.ajax({
            url: $('#led-1').is(':checked') ? "http://localhost:5000/call/led-1/turn_on" : "http://localhost:5000/call/led-1/turn_off",
            type: 'GET',
            success: function (response) {
            }
        });
    });
});