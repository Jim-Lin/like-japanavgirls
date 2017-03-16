// Set up context menu tree at install time.
chrome.runtime.onInstalled.addListener(function() {
  chrome.contextMenus.create({
    title: "Like Japanavgirls",
    contexts: ["image"],
    id: "image"
  });
});

chrome.contextMenus.onClicked.addListener(onClickHandler);

function onClickHandler(info, tab) {
    // The srcUrl property is only available for image elements.
    var url = 'info.html#' + info.srcUrl;

    // Create a new window to the info page.
    chrome.windows.create({ url: url, width: 560, height: 560, type: "popup" });
}