const { app, BrowserWindow, ipcMain, dialog } = require('electron');
const path = require('path');
const fetch = require('node-fetch');
const isDev = process.argv.includes('--dev');

let mainWindow;

function createWindow() {
  // Create the browser window
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    minWidth: 800,
    minHeight: 600,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      enableRemoteModule: false,
      preload: path.join(__dirname, 'preload.js')
    },
    icon: path.join(__dirname, 'assets', 'icon.png'), // Optional: add an icon
    titleBarStyle: 'default',
    show: false, // Don't show until ready
    backgroundColor: '#0f172a' // Match the dark theme
  });

  // Load the app
  if (isDev) {
    // In development, load from Vite dev server
    console.log('Loading from Vite dev server: http://localhost:5173');
    mainWindow.loadURL('http://localhost:5173').then(() => {
      console.log('Successfully loaded from Vite dev server');
    }).catch((error) => {
      console.error('Failed to load from Vite dev server:', error);
      console.log('Trying to load fallback file...');
      // Try to load the built files as fallback
      mainWindow.loadFile(path.join(__dirname, 'renderer', 'index.html')).catch((fallbackError) => {
        console.error('Failed to load fallback file:', fallbackError);
        // Show an error dialog
        dialog.showErrorBox('Loading Error', 
          'Failed to load the application.\n\n' +
          'Please make sure the Vite dev server is running:\n' +
          'npm run dev:vite\n\n' +
          'Or build the app first:\n' +
          'npm run build'
        );
      });
    });
    mainWindow.webContents.openDevTools();
  } else {
    // In production, load the built files
    console.log('Loading from built files');
    mainWindow.loadFile(path.join(__dirname, 'renderer', 'index.html'));
  }

  // Show window when ready to prevent visual flash
  mainWindow.once('ready-to-show', () => {
    mainWindow.show();
  });

  // Handle window closed
  mainWindow.on('closed', () => {
    mainWindow = null;
  });

  // Handle external links
  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    require('electron').shell.openExternal(url);
    return { action: 'deny' };
  });
}

// This method will be called when Electron has finished initialization
app.whenReady().then(() => {
  createWindow();

  app.on('activate', () => {
    // On macOS it's common to re-create a window in the app when the
    // dock icon is clicked and there are no other windows open.
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});

// Quit when all windows are closed, except on macOS
app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

// IPC handlers for communication between main and renderer processes
ipcMain.handle('show-error-dialog', async (event, title, content) => {
  const result = await dialog.showErrorBox(title, content);
  return result;
});

ipcMain.handle('show-info-dialog', async (event, title, content) => {
  const result = await dialog.showMessageBox(mainWindow, {
    type: 'info',
    title: title,
    message: content,
    buttons: ['OK']
  });
  return result;
});

ipcMain.handle('show-confirmation-dialog', async (event, title, content) => {
  const result = await dialog.showMessageBox(mainWindow, {
    type: 'question',
    title: title,
    message: content,
    buttons: ['Yes', 'No'],
    defaultId: 0,
    cancelId: 1
  });
  return result.response === 0;
});

// Handle backend connection status
ipcMain.handle('check-backend-status', async () => {
  try {
    const response = await fetch('http://127.0.0.1:4000/health');
    return { status: 'connected', data: await response.json() };
  } catch (error) {
    return { status: 'disconnected', error: error.message };
  }
});

// Handle form submission to backend
ipcMain.handle('submit-form', async (event, payload) => {
  try {
    const response = await fetch('http://127.0.0.1:4000/api/submissions', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    
    const result = await response.json();
    return { success: response.ok, data: result, error: response.ok ? null : result.error };
  } catch (error) {
    return { success: false, data: null, error: error.message };
  }
});

// Security: Prevent new window creation
app.on('web-contents-created', (event, contents) => {
  contents.on('new-window', (event, navigationUrl) => {
    event.preventDefault();
    require('electron').shell.openExternal(navigationUrl);
  });
});
