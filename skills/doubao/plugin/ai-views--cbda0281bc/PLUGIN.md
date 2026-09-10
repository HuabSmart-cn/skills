{
  "manifest_version": 3,
  "name": "__MSG_name__",
  "description": "__MSG_description__",
  "default_locale": "zh_CN",
  "version": "1.0.2.511",
  "icons": {
    "16": "assets/icon.png",
    "32": "assets/icon.png",
    "48": "assets/icon.png",
    "128": "assets/icon.png"
  },
  "background": {
    "service_worker": "static/js/background.js",
    "type": "module"
  },
  "action": {
    "default_icon": {
      "16": "assets/icon.png",
      "32": "assets/icon.png",
      "48": "assets/icon.png",
      "128": "assets/icon.png"
    },
    "default_title": ""
  },
  "side_panel": {
    "default_path": "side_panel.html"
  },
  "permissions": [
    "storage",
    "cookies",
    "tabs",
    "webRequest",
    "sidePanel",
    "scripting",
    "contextMenus",
    "declarativeNetRequest",
    "declarativeNetRequestWithHostAccess",
    "declarativeNetRequestFeedback",
    "webNavigation",
    "bookmarks"
  ],
  "options_ui": {
    "page": "options.html",
    "open_in_tab": true
  },
  "content_scripts": [
    {
      "matches": [
        "<all_urls>"
      ],
      "js": [
        "static/js/82657.js",
        "static/js/42895.js",
        "static/js/73781.js",
        "static/js/73415.js",
        "static/js/71081.js",
        "static/js/47173.js",
        "static/js/46539.js",
        "static/js/8588.js",
        "static/js/57237.js",
        "static/js/25913.js",
        "static/js/68452.js",
        "static/js/7359.js",
        "static/js/5058.js",
        "static/js/39694.js",
        "static/js/content.js"
      ],
      "exclude_matches": [
        "https://www.doubao.com/chat/**",
        "https://www.cici.com/chat/**",
        "https://www.ciciai.com/chat/**",
        "https://www.dola.com/chat/**",
        "https://www.doubao.com/1b9d6bcd-bbfd-4b2d-9b5d-ab8dfbbd4bed",
        "https://www.cici.com/1b9d6bcd-bbfd-4b2d-9b5d-ab8dfbbd4bed",
        "https://www.doubao.com/cross-site-support",
        "https://www.cici.com/cross-site-support",
        "https://www.dola.com/cross-site-support"
      ],
      "run_at": "document_end"
    },
    {
      "matches": [
        "<all_urls>"
      ],
      "js": [
        "static/js/preinject.js"
      ],
      "run_at": "document_start"
    },
    {
      "matches": [
        "https://www.doubao.com/chat/**",
        "https://www.cici.com/chat/**",
        "https://www.ciciai.com/chat/**",
        "https://www.dola.com/chat/**"
      ],
      "js": [
        "static/js/homepage_scripts.js"
      ],
      "run_at": "document_start"
    }
  ],
  "host_permissions": [
    "<all_urls>"
  ],
  "commands": {},
  "web_accessible_resources": [
    {
      "matches": [
        "<all_urls>"
      ],
      "resources": [
        "assets/icon*.png",
        "static/css/*",
        "static/svg/*",
        "static/image/*",
        "configs/*",
        "cdn-media-assets/*",
        "*.json"
      ]
    }
  ],
  "externally_connectable": {
    "matches": [
      "https://*.doubao.com/*",
      "https://*.cici.com/*",
      "https://*.ciciai.com/*",
      "https://*.dola.com/*",
      "https://*.larkoffice.com/*",
      "https://*.feishu.cn/*"
    ]
  },
  "key": "MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAobM/wjbnOqNnYUqjgwNklGVXvvh1xweX5D9FFurAhscXOQN/mytnS3gxGEPGCBWwbMYEs0NVtrZAsORgqAsQQ50gDUoQJ2T4OFrHSEsI7a3Rb7fjF7xBsqPBYwaveX4Jzqb2HXrzXe1wR7cSV+ypC3gYKuzpZRpIDOpsHRN20ClRZKUwrfmEfVg6kcCeLw/DqFoT4gXE6h7jHsTLulQLGi344X8tU1UNkvHftMboaWoEubO9dS0hmHZQNAeDz50eKRHg9FQIbgZYqXXbJUSDHoetlAlZBJ6sJ/vtwQJIaBwVpH/9Hx3fbCKK6ss/b0mPgFo8DmKKyeHTxVDiA4Lq5wIDAQAB"
}