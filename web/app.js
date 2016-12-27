(function () {
    var filename;

    var uploadImage = document.querySelector('#uploadImage');
    uploadImage.addEventListener('change', function () {
        filename = this.value.replace(/^.*?([^\\\/]*)$/, '$1');
        preview(this.files[0]);
        upload(this.files[0]);
    }, false);

    function preview(file) {
        var result = document.getElementById("result");
        while (result.firstChild) {
            result.removeChild(result.firstChild);
        }

        var preview = document.getElementById("preview");
        while (preview.firstChild) {
            preview.removeChild(preview.firstChild);
        }

        var thumb = document.createElement("div");
        thumb.classList.add('block');

        var img = document.createElement("img");
        img.file = file;

        thumb.appendChild(img);
        preview.appendChild(thumb);

        // Using FileReader to display the image content
        var reader = new FileReader();
        reader.onload = (function(aImg) { return function(e) { aImg.src = e.target.result; }; })(img);
        reader.readAsDataURL(file);
    }

    function result(json) {
        var result = document.getElementById("result");

        var thumb = document.createElement("div");
        thumb.classList.add('block');

        if(json.Name == "") {
            var h3 = document.createElement("h3");
            var notfound = document.createTextNode("找不到");
            h3.appendChild(notfound);

            thumb.appendChild(h3);
            result.appendChild(thumb);

            return;
        }

        var h3 = document.createElement("h3");
        var name = document.createTextNode(json.Name);
        h3.appendChild(name);

        var img = document.createElement("img");
        img.src = json.Img;
        var a_img = document.createElement("a");
        a_img.setAttribute("href", "http://sp.dmm.co.jp/mono/list/index/shop/dvd/article/actress/id/" + json.Id + "/sort/date");
        a_img.appendChild(img);

        var div_similarity = document.createElement("div");
        var similarity = document.createTextNode("相似度: " + json.Similarity);
        div_similarity.appendChild(similarity);

        var div_resource = document.createElement("div");
        var a_buy = document.createElement("a");
        var t_buy = document.createTextNode("去買片");
        a_buy.setAttribute("href", "http://www.r18.com/videos/vod/movies/list/id=" + json.Id + "/sort=new/type=actress/");
        a_buy.appendChild(t_buy);
        var a_torrent = document.createElement("a");
        var t_torrent = document.createTextNode("去抓片");
        a_torrent.setAttribute("href", "http://sukebei.nyaa.se/?page=search&term=" + json.Name);
        a_torrent.appendChild(t_torrent);
        div_resource.appendChild(a_buy);
        div_resource.appendChild(document.createTextNode(" "));
        div_resource.appendChild(a_torrent);

        var div_feedback = document.createElement("div");
        var b_like = document.createElement("button");
        b_like.setAttribute("id", "like");
        var t_like = document.createTextNode("覺得像");
        b_like.appendChild(t_like);
        var b_unlike = document.createElement("button");
        b_unlike.setAttribute("id", "unlike");
        var t_unlike = document.createTextNode("差很多");
        b_unlike.appendChild(t_unlike);
        div_feedback.appendChild(b_like);
        div_feedback.appendChild(document.createTextNode(" "));
        div_feedback.appendChild(b_unlike);
        
        thumb.appendChild(h3);
        thumb.appendChild(a_img);
        thumb.appendChild(div_similarity);
        thumb.appendChild(document.createElement("br"));
        thumb.appendChild(div_resource);
        thumb.appendChild(document.createElement("br"));
        thumb.appendChild(div_feedback);
        result.appendChild(thumb);
    }

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
                result(json);
            }
        };
        fd.append('upload', file);
        xhr.send(fd);

        uploadImage.value = "";
    }
}());