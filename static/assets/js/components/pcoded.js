// Existing JavaScript content remains here

$(document).ready(function(){
    $(".navbar-toggler").click(function(){
        $(".navbar-collapse").slideToggle(300);
    });

    // Set active class on the current page link
    var path = window.location.pathname.split("/").pop();
    if (path == '') {
        path = 'index.html';
    }
    $('.navbar-nav .nav-link').each(function() {
        if ($(this).attr('href') === path) {
            $(this).addClass('active');
        }
    });
});

$(window).on('resize', function(){
    setTimeout(function(){ test(); }, 500);
});
