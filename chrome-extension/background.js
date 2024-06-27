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
    var url = 'info.html#' + decodeURIComponent(info.srcUrl);

    // Create a new window to the info page.
    chrome.windows.create({ url: url, width: 560, height: 720, type: "popup" });

    const rules = [{
        "id": 1,
        "action": {
            "type": "modifyHeaders",
            "requestHeaders": [{
                "header": "Referer",
                "operation": "set",
                "value": (new URL(tab.url)).origin,
            }]
        },
        "condition": {
            "urlFilter": "https://like-av.xyz/api/*",
            "resourceTypes": ["xmlhttprequest"] // see available https://developer.chrome.com/docs/extensions/reference/declarativeNetRequest/#type-ResourceType
        }
    }];
    chrome.declarativeNetRequest.updateDynamicRules({
        removeRuleIds: rules.map(r => r.id),
        addRules: rules,
    });
}
