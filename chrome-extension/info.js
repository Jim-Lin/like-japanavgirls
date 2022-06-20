(function () {
    String.defaultLocale = "en";
    var l = function (string) {
        return string.toLocaleString();
    };

    var error = document.getElementById("error").firstChild;
    error.nodeValue = l("%error");

    var filename;

    var feedback = function(id, ox) {
        var url = "https://like-av.xyz/api/feedback";
        var xhr = new XMLHttpRequest();

        xhr.open("POST", url, true);
        xhr.send(JSON.stringify({id: id, ox: ox, file: filename}));

        var b = document.createElement("b");
        b.setAttribute("style", "text-align: center;");
        var thx = document.createTextNode("Thanks");
        b.appendChild(thx);

        var feedback = document.getElementById("feedback" + id);
        while (feedback.firstChild) {
            feedback.removeChild(feedback.firstChild);
        }

        feedback.appendChild(b);
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
        var process = document.getElementById("process");
        process.style.display = "block";

        var result = document.getElementById("result");

        result.appendChild(createCard(json.Data[0]));
        // json.Data.forEach(function(element, index, array) {
        //     result.appendChild(createCard(element));
        // });

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
        card.classList.add('card');
        card.classList.add('fadeOut');

        var div_profile = document.createElement("div");
        div_profile.classList.add('profile');
        var img = document.createElement("img");
        img.src = json.Img;

        var div_name = document.createElement("div");
        div_name.classList.add('name');
        var name = document.createTextNode(json.Name);
        div_name.appendChild(name);

        var div_similarity = document.createElement("div");
        div_similarity.classList.add('similarity');
        // var similarity = document.createTextNode("そっくり率: " + json.Similarity + "%");
        var similarity = document.createTextNode(l("%similarity") + ": " + json.Similarity + "%");
        div_similarity.appendChild(similarity);

        /*
        var div_feedback = document.createElement("div");
        div_feedback.setAttribute("id", "feedback" + json.Id);
        div_feedback.classList.add('feedback');
        var div_like = document.createElement("div");
        div_like.setAttribute("id", "like");
        div_like.addEventListener('click', function(event) {
            feedback(json.Id, "like");
        });
        // var t_like = document.createTextNode("そっくり");
        var t_like = document.createTextNode(l("%like"));
        div_like.appendChild(t_like);
        var div_unlike = document.createElement("div");
        div_unlike.setAttribute("id", "unlike");
        div_unlike.addEventListener('click', function(event) {
            feedback(json.Id, "unlike");
        });
        // var t_unlike = document.createTextNode("似てない");
        var t_unlike = document.createTextNode(l("%unlike"));
        div_unlike.appendChild(t_unlike);
        var div_center = document.createElement("div");
        div_center.setAttribute("id", "center");
        div_feedback.appendChild(div_unlike);
        div_feedback.appendChild(div_center);
        div_feedback.appendChild(div_like);
        */

        card.appendChild(div_profile);
        card.appendChild(div_name);
        card.appendChild(div_similarity);

        var div_separation = document.createElement("div");
        div_separation.classList.add('separation');
        div_separation.appendChild(document.createElement("hr"));
        card.appendChild(div_separation);

        // card.appendChild(div_feedback);

        return card;
    }

    /**
     * Upload a file
     * @param file
     */
    function upload(file) {
        // show the loading image
        var loading = document.getElementById("loading");
        loading.style.display = "block";

        var url = "https://like-av.xyz/api/upload";
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
                    var preview = document.getElementById("preview");
                    preview.classList.remove('col-8');
                    preview.classList.add('col-5');

                    return;
                }

                filename = json.File;
                result(json);
            }
        };
        fd.append('upload', file, filename);
        xhr.send(fd);
    }

    document.addEventListener("DOMContentLoaded", function() {
        var imageUrl = window.location.hash.substring(1);
        if (imageUrl) {
            filename = imageUrl.match(/[^\/?#%]+(?=$|[?#%])/);

            var request = new XMLHttpRequest();
            request.responseType = "blob";
            request.onload = function() {
                preview(request.response);
                upload(request.response);
            };
            request.open("GET", imageUrl);
            request.send();
        }
    });
}());
