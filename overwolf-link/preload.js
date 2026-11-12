const { contextBridge, ipcRenderer } = require("electron");

contextBridge.exposeInMainWorld("link", {
  onStatus: cb => ipcRenderer.on("status", (e, s) => cb(s)),
  setHud: url => ipcRenderer.send("set-hud", url),
  setTestChannel: on => ipcRenderer.send("set-test-channel", on),
});
