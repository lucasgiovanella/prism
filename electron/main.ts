import { app, BrowserWindow, ipcMain, dialog, shell } from 'electron';
import path from 'path';
import { spawn, ChildProcess } from 'child_process';
import fs from 'fs/promises';
import { existsSync } from 'fs';

let mainWindow: BrowserWindow | null = null;
let pythonProcess: ChildProcess | null = null;

const isDev = process.env.NODE_ENV === 'development' || !app.isPackaged;

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1280,
    height: 800,
    minWidth: 1024,
    minHeight: 600,
    backgroundColor: '#050816', // Matches tailwind background
    icon: path.join(__dirname, '../src/assets/icons/icon.png'),
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      nodeIntegration: false,
      contextIsolation: true,
    },
    autoHideMenuBar: true, // Hide the default menu bar
  });

  if (isDev) {
    mainWindow.loadURL('http://localhost:5173');
  } else {
    mainWindow.loadFile(path.join(__dirname, '../dist/index.html'));
  }
}

// --- Python Backend Management ---

function startPythonBackend() {
  const scriptPath = path.join(__dirname, '../backend/api.py');

  let pythonPath = 'python';
  if (process.platform === 'win32') {
    const venvPython = path.join(__dirname, '../venv/Scripts/python.exe');
    if (require('fs').existsSync(venvPython)) {
      pythonPath = venvPython;
    }
  } else {
    const venvPython = path.join(__dirname, '../venv/bin/python');
    if (require('fs').existsSync(venvPython)) {
      pythonPath = venvPython;
    }
  }

  console.log(`Starting Python backend with: ${pythonPath}`);
  pythonProcess = spawn(pythonPath, [scriptPath], {
    stdio: 'inherit', // Pipe output to main console
    windowsHide: true, // Hide the terminal window
  });

  pythonProcess.on('error', (err) => {
    console.error('Failed to start Python backend:', err);
  });

  pythonProcess.on('exit', (code, signal) => {
    console.log(`Python backend exited with code ${code} and signal ${signal}`);
  });
}

function killPythonBackend() {
  if (pythonProcess) {
    console.log('Killing Python backend...');
    pythonProcess.kill();
    pythonProcess = null;
  }
}

// --- IPC Handlers (Markdown Export) ---

ipcMain.handle('save-tutorial', async (event, { title, steps }) => {
  try {
    // Prompt user for directory
    const { canceled, filePaths } = await dialog.showOpenDialog(mainWindow!, {
      title: 'Selecionar pasta para salvar o tutorial',
      properties: ['openDirectory', 'createDirectory'],
    });

    if (canceled || filePaths.length === 0) {
      return { success: false, message: 'Cancelado pelo usuário.' };
    }

    const outputDir = filePaths[0];
    const tutorialDirName = title.replace(/[^a-z0-9]/gi, '_').toLowerCase();
    const tutorialPath = path.join(outputDir, tutorialDirName);
    const assetsPath = path.join(tutorialPath, 'assets');

    if (!existsSync(tutorialPath)) {
      await fs.mkdir(tutorialPath, { recursive: true });
    }
    if (!existsSync(assetsPath)) {
      await fs.mkdir(assetsPath, { recursive: true });
    }

    let markdownContent = `# ${title}\n\n`;

    for (let i = 0; i < steps.length; i++) {
      const step = steps[i];
      const stepNum = i + 1;
      const imgFileName = `step_${stepNum}.png`;
      const imgPath = path.join(assetsPath, imgFileName);

      // Save image (base64 to file)
      if (step.image) {
        const base64Data = step.image.replace(/^data:image\/png;base64,/, "");
        await fs.writeFile(imgPath, base64Data, 'base64');
      }

      markdownContent += `## Passo ${stepNum}\n\n`;

      if (step.content_type === 'code') {
        const lang = step.code_language || '';
        markdownContent += '```' + lang + '\n';
        markdownContent += (step.code_content || '') + '\n';
        markdownContent += '```\n\n';
      } else {
        markdownContent += `${step.description}\n\n`;
      }

      if (step.image) {
        markdownContent += `![Passo ${stepNum}](./assets/${imgFileName})\n\n`;
      }
    }

    const mdPath = path.join(tutorialPath, 'manual.md');
    await fs.writeFile(mdPath, markdownContent, 'utf-8');

    // Open folder
    shell.openPath(tutorialPath);

    return { success: true, path: tutorialPath };
  } catch (error: any) {
    console.error('Export error:', error);
    return { success: false, message: error.message };
  }
});

// --- Lifecycle ---

app.whenReady().then(() => {
  startPythonBackend();
  createWindow();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('will-quit', () => {
  killPythonBackend();
});
