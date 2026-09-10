{
  "manifest_version": 3,
  "name": "豆包浏览器自动化助手",
  "version": "0.21.24",
  "key": "MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEArm8IjPvtAY39KVhQq7aKD5gkp9RdFT1SAH5UugwYRjSZN/UfqmbSpAYn+uh2g+KQLpGaGmZGUbmRKuWi+hzsTP0cEFo0MrhrkwW5pBw3gY5nXBZaGJIBb7qR3HKyzSR7s93m7nxb+0Uk8YpfOEZCWMNx9vNSbuBYSN38TS+tOMHHoOWHHa1iKJc4X2rL8RNaFbOwNgGKFkCKP4aFwTpCROUoOnwNlZh5tJi2ANQiH/vTbbVQqC0kQQrrvFqOyXIwS+121zprUmSQoJ5QUIa91W4ytu625sl+OS/daYkzi/SDVFeYLbE71pEWNvYyTytk55Ylm8Z827TWSk63sjUOiQIDAQAB",
  "description": "在你的允许下，让智能助手使用豆包内置浏览器完成自动化任务。",
  "permissions": [
    "debugger",
    "tabs",
    "tabGroups",
    "activeTab",
    "alarms",
    "storage",
    "unlimitedStorage",
    "nativeMessaging",
    "downloads"
  ],
  "host_permissions": [
    "<all_urls>",
    "http://127.0.0.1/*"
  ],
  "background": {
    "service_worker": "background.js"
  },
  "icons": {
    "16": "icons/icon-16.png",
    "32": "icons/icon-32.png",
    "48": "icons/icon-48.png",
    "128": "icons/icon-128.png"
  },
  "action": {
    "default_popup": "popup.html",
    "default_title": "豆包浏览器自动化助手",
    "default_icon": {
      "16": "icons/icon-16.png",
      "32": "icons/icon-32.png",
      "48": "icons/icon-48.png",
      "128": "icons/icon-128.png"
    }
  }
}