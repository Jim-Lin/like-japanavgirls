String.defaultLocale = "en";
const l = function (string) {
    return string.toLocaleString();
};

const error = document.getElementById("error").firstChild;
error.nodeValue = l("%error");

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

async function upload(file, filename) {
    // show the loading image
    var loading = document.getElementById("loading");
    loading.style.display = "block";

    const url = "https://like-av.xyz/api/upload";
    const fd = new FormData();
    fd.append('upload', file, filename);
    try {
        const response = await fetch(url, {
            method: "POST",
            body: fd,
        });
        const json = await response.json();
        // console.log("Success:", json);

        // now hide the loading image
        loading.style.display = "none";
        if ((Object.keys(json).length === 0 && json.constructor === Object) || (json.Count == 0)) {
            var notfound = document.getElementById("notfound");
            notfound.style.display = "block";
            var preview = document.getElementById("preview");
            preview.classList.remove('col-8');
            preview.classList.add('col-5');

            return;
        }

        return json;
      } catch (error) {
        // console.error("Error:", error);
      }
}

function result(json) {
    var process = document.getElementById("process");
    process.style.display = "block";

    var result = document.getElementById("result");

    result.appendChild(createCard(json.Data[0]));
    if (json.Data[1]) {
        result.appendChild(createCard(json.Data[1]));
    }

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
    div_profile.appendChild(img);

    var div_name = document.createElement("div");
    div_name.classList.add('name');
    var name = document.createTextNode(json.Name);
    div_name.appendChild(name);

    var div_similarity = document.createElement("div");
    div_similarity.classList.add('similarity');
    var similarity = document.createTextNode(l("%similarity") + ": " + json.Similarity + "%");
    div_similarity.appendChild(similarity);

    card.appendChild(div_profile);
    card.appendChild(div_name);
    card.appendChild(div_similarity);

    return card;
}

document.addEventListener("DOMContentLoaded", async function() {
    var imageUrl = window.location.hash.substring(1);
    if (imageUrl) {
        const req = new Request(imageUrl);
        const json = await fetch(req)
        .then((response) => response.blob())
        .then((blob) => {
            preview(blob);
            const filename = imageUrl.match(/[^\/?#%]+(?=$|[?#%])/);

            return upload(blob, filename);
        });
        if (json) {
            result(json);
        }
    }
});
