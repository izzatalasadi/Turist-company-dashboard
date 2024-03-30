(function($) {
  'use strict';
  $(function() {
      var proBanner = document.querySelector('#proBanner');
      var navbar = document.querySelector('.navbar');
      var pageBodyWrapper = document.querySelector('.page-body-wrapper');

      if ($.cookie('DMC-Nordic')!="true") {
          if (proBanner) proBanner.classList.add('d-flex');
          if (navbar) navbar.classList.remove('fixed-top');
      } else {
          if (proBanner) proBanner.classList.add('d-none');
          if (navbar) navbar.classList.add('fixed-top');
      }
      
      if (navbar && $(navbar).hasClass("fixed-top")) {
          if (pageBodyWrapper) pageBodyWrapper.classList.remove('pt-0');
          if (navbar) navbar.classList.remove('pt-5');
      } else {
          if (pageBodyWrapper) pageBodyWrapper.classList.add('pt-0');
          if (navbar) {
              navbar.classList.add('pt-5');
              navbar.classList.add('mt-3');
          }
      }

      var bannerClose = document.querySelector('#bannerClose');
      if (bannerClose) {
          bannerClose.addEventListener('click', function() {
              if (proBanner) {
                  proBanner.classList.add('d-none');
                  proBanner.classList.remove('d-flex');
              }
              if (navbar) {
                  navbar.classList.remove('pt-5');
                  navbar.classList.add('fixed-top');
                  navbar.classList.remove('mt-3');
              }
              if (pageBodyWrapper) pageBodyWrapper.classList.add('proBanner-padding-top');
              
              var date = new Date();
              date.setTime(date.getTime() + 24 * 60 * 60 * 1000); 
              $.cookie('DMC-Nordic', "true", { expires: date });
          });
      }
  })
})(jQuery);
