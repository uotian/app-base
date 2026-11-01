import { contextBridge, ipcRenderer } from "electron";
import type { DesktopBridge } from "../../shared/contracts";

const bridge: DesktopBridge = {
  getEnvironment: () => ipcRenderer.invoke("environment:get"),
  getGreeting: () => ipcRenderer.invoke("greeting:get"),
};

contextBridge.exposeInMainWorld("desktop", bridge);
