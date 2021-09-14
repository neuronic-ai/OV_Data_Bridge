
//for sidebar

$(".collapse-panel").click(function(){
  $(".sidenav").toggleClass("collapse");
});

// $(document).mouseup(function (e) {
//     if ($(e.target).closest(".sidenav.active").length
//                 === 0) {
//         $(".sidenav.active").hide();
//     }
// });


//for sidebar menu toggle

$(".menu-toggle").click(function(){
  $(".sidenav").toggleClass("active");
});

//for search toggle toggle

$(".mobile-search").click(function(){
  $(".search-bar").toggleClass("active");
});

$(".close-toggle").click(function(){
  $(".search-bar").removeClass("active");
});
