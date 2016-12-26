/**
 * Created by remi on 18/01/15.
 */
(function(){



    function previewImage(file) {
        var galleryId = "gallery";

        var gallery = document.getElementById(galleryId);
        var imageType = /image.*/;

        if (!file.type.match(imageType)) {
            throw "File Type must be an image";
        }

        var thumb = document.createElement("div");
        // thumb.classList.add('thumbnail');

        var img = document.createElement("img");
        img.file = file;
        thumb.appendChild(img);
        gallery.appendChild(thumb);

        // Using FileReader to display the image content
        var reader = new FileReader();
        reader.onload = (function(aImg) { return function(e) { aImg.src = e.target.result; }; })(img);
        reader.readAsDataURL(file);
    }

    var uploadfiles = document.querySelector('#fileinput');
    uploadfiles.addEventListener('change', function () {
        var files = this.files;
        for(var i=0; i<files.length; i++){
            previewImage(this.files[i]);
        }

    }, false);
})();