/**
 * Created by remi on 17/01/15.
 */
(function () {

    var uploadImage = document.querySelector('#uploadImage');
    uploadImage.addEventListener('change', function () {
        var files = this.files;
        for(var i=0; i<files.length; i++){
            upload(this.files[i]);
        }

    }, false);


    /**
     * Upload a file
     * @param file
     */
    function upload(file){
        var url = "http://like-av.xyz:9090/upload";
        var xhr = new XMLHttpRequest();
        var fd = new FormData();
        xhr.open("POST", url, true);
        xhr.onreadystatechange = function() {
            if (xhr.readyState == 4 && xhr.status == 200) {
                // Every thing ok, file uploaded
                var json = JSON.parse(xhr.responseText);
                console.log(json); // handle response.
            }
        };
        fd.append('upload', file);
        xhr.send(fd);
    }
}());