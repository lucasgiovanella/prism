import { contextBridge, ipcRenderer } from 'electron';

contextBridge.exposeInMainWorld('electronAPI', {
  saveTutorial: (data: any) => ipcRenderer.invoke('save-tutorial', data),
  onExportResult: (callback: (event: any, result: any) => void) => ipcRenderer.on('export-result', callback),
});
