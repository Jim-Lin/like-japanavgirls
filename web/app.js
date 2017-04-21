(function () {
    var filename;

    var uploadImage = document.querySelector('#uploadImage');
    uploadImage.addEventListener('change', function() {
        filename = this.value.replace(/^.*?([^\\\/]*)$/, '$1');
        preview(this.files[0]);
        upload(this.files[0]);
    }, false);

    var feedback = function(id, ox) {
        var url = "http://like-av.xyz/api/feedback";
        var xhr = new XMLHttpRequest();

        xhr.open("POST", url, true);
        xhr.onreadystatechange = function() {
            if (xhr.readyState == 4 && xhr.status == 200) {
                var b = document.createElement("b");
                b.setAttribute("style", "text-align: center;");
                var thx = document.createTextNode("Thanks");
                b.appendChild(thx);

                var feedback = document.getElementById("feedback" + id);
                while (feedback.firstChild) {
                    feedback.removeChild(feedback.firstChild);
                }

                feedback.appendChild(b);
            }
        };

        xhr.send(JSON.stringify({id: id, ox: ox, file: filename}));
    };

    function preview(file) {
        var result = document.getElementById("result");
        while (result.firstChild) {
            result.removeChild(result.firstChild);
        }

        var preview = document.getElementById("preview");
        while (preview.firstChild) {
            preview.removeChild(preview.firstChild);
        }

        var notfound = document.getElementById("notfound");
        notfound.style.display = "none";

        var img = document.createElement("img");
        img.file = file;
        img.classList.add('thumb');

        preview.appendChild(img);

        // Using FileReader to display the image content
        var reader = new FileReader();
        reader.onload = (function(aImg) { return function(e) { aImg.src = e.target.result; }; })(img);
        reader.readAsDataURL(file);
    }

    function result(json) {
        var result = document.getElementById("result");

        json.Data.forEach(function(element, index, array) {
            result.appendChild(createCard(element));
        });


        var controls = document.querySelector('.upload-controls');
        if ((controls.offsetTop-window.scrollY) < 10) {
            window.scrollTo(0, 0);
        }

        scrollToItem(controls);

        // querySelectorAll support issue
        // document.querySelectorAll('.fadeOut').forEach(function(element, index, array) {
        //     element.classList.remove('fadeOut');
        // });

        var divs = [].slice.call(document.querySelectorAll('div')).filter(function(el) {
           return el.className.match(/\bfadeOut\b/i);
        });
        divs.forEach(function(element, index, array) {
            element.classList.remove('fadeOut');
        });
    }

    function createCard(json) {
        var card = document.createElement("div");
        card.classList.add('card', 'fadeOut');

        var div_profile = document.createElement("div");
        div_profile.classList.add('profile');
        var img = document.createElement("img");
        img.src = json.Img;
        var a_img = document.createElement("a");
        a_img.setAttribute("href", "http://sp.dmm.co.jp/mono/list/index/shop/dvd/article/actress/id/" + json.Id + "/sort/date");
        a_img.setAttribute("target", "_blank");
        a_img.appendChild(img);
        div_profile.appendChild(a_img);

        var div_name = document.createElement("div");
        div_name.classList.add('name');
        var name = document.createTextNode(json.Name);
        div_name.appendChild(name);

        var div_similarity = document.createElement("div");
        div_similarity.classList.add('similarity');
        var similarity = document.createTextNode("そっくり率: " + json.Similarity + "%");
        div_similarity.appendChild(similarity);

        var div_buy = document.createElement("div");
        div_buy.classList.add('button-box', 'box');
        var t_buy = document.createTextNode("買い物に行く");
        var a_buy = document.createElement("a");
        a_buy.classList.add('button');
        a_buy.setAttribute("href", "http://www.r18.com/videos/vod/movies/list/id=" + json.Id + "/sort=new/type=actress/");
        a_buy.setAttribute("target", "_blank");
        a_buy.appendChild(t_buy);
        div_buy.appendChild(a_buy);

        var div_feedback = document.createElement("div");
        div_feedback.setAttribute("id", "feedback" + json.Id);
        div_feedback.classList.add('feedback');
        var div_like = document.createElement("div");
        div_like.setAttribute("id", "like");
        div_like.addEventListener('click', function(event) {
            feedback(json.Id, "like");
        });
        var t_like = document.createTextNode("そっくり");
        div_like.appendChild(t_like);
        var div_unlike = document.createElement("div");
        div_unlike.setAttribute("id", "unlike");
        div_unlike.addEventListener('click', function(event) {
            feedback(json.Id, "unlike");
        });
        var t_unlike = document.createTextNode("似てない");
        div_unlike.appendChild(t_unlike);
        var div_center = document.createElement("div");
        div_center.setAttribute("id", "center");
        div_feedback.appendChild(div_unlike);
        div_feedback.appendChild(div_center);
        div_feedback.appendChild(div_like);
        
        card.appendChild(div_profile);
        card.appendChild(div_name);
        card.appendChild(div_similarity);
        card.appendChild(div_buy);

        var div_separation = document.createElement("div");
        div_separation.classList.add('separation');
        div_separation.appendChild(document.createElement("hr"));
        card.appendChild(div_separation);

        card.appendChild(div_feedback);

        return card;
    }

    /**
     * Upload a file
     * @param file
     */
    function upload(file) {
        var process = document.getElementById("process");
        process.style.display = "block";
        // show the loading image
        var loading = document.getElementById("loading");
        loading.style.display = "block";

        var url = "http://like-av.xyz/api/upload";
        var xhr = new XMLHttpRequest();
        var fd = new FormData();
        xhr.open("POST", url, true);
        xhr.onreadystatechange = function() {
            if (xhr.readyState == 4 && xhr.status == 200) {
                // now hide the loading image
                loading.style.display = "none";

                // Every thing ok, file uploaded
                var json = JSON.parse(xhr.responseText);
                console.log(json); // handle response.

                if ((Object.keys(json).length === 0 && json.constructor === Object) || (json.Count == 0)) {
                    var notfound = document.getElementById("notfound");
                    notfound.style.display = "block";

                    return;
                }

                filename = json.File;
                result(json);
            }
        };
        fd.append('upload', file);
        xhr.send(fd);

        uploadImage.value = "";
    }

    var tmpScrollY = -1;
    function scrollToItem(item) {
        var diff = (item.offsetTop-window.scrollY) / 10;
        if (Math.abs(diff) > 0 && tmpScrollY != window.scrollY) {
            tmpScrollY = window.scrollY;
            window.scrollTo(0, (window.scrollY+diff));
            clearTimeout(window._TO);
            window._TO = setTimeout(scrollToItem, 10, item);
        } else {
            clearTimeout(window._TO);
            window.scrollTo(0, item.offsetTop)
        }
    }
}());