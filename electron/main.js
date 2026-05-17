const { app, BrowserWindow, ipcMain, dialog, shell } = require('electron')
const path = require('path')
const { spawn } = require('child_process')

const isDev = process.env.NODE_ENV !== 'production'
const BACKEND_PORT = 8765

let mainWindow = null
let engineProcess = null

// ---------------------------------------------------------------------------
// Python engine sidecar
// ---------------------------------------------------------------------------

function startEngine() {
  const engineDir = path.join(__dirname, '..', 'engine')

  // On Windows, prefer python.exe in venv; fall back to system python
  const pythonExe = process.platform === 'win32' ? 'python' : 'python3'

  engineProcess = spawn(
    pythonExe,
    ['-m', 'uvicorn', 'main:app', '--host', '127.0.0.1', '--port', String(BACKEND_PORT)],
    {
      cwd: engineDir,
      windowsHide: true,
      env: { ...process.env, PYTHONUNBUFFERED: '1' },
    }
  )

  engineProcess.stdout.on('data', (d) => {
    if (isDev) console.log('[engine]', d.toString().trim())
  })
  engineProcess.stderr.on('data', (d) => {
    if (isDev) console.error('[engine]', d.toString().trim())
  })
  engineProcess.on('error', (err) => {
    console.error('Failed to start Python engine:', err.message)
  })
}

// ---------------------------------------------------------------------------
// Window
// ---------------------------------------------------------------------------

function createWindow() {
  mainWindow = new BrowserWindow({
    width:  1440,
    height: 900,
    minWidth:  1024,
    minHeight: 700,
    backgroundColor: '#050c14',
    titleBarStyle: process.platform === 'darwin' ? 'hiddenInset' : 'default',
    webPreferences: {
      preload:          path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration:  false,
    },
    icon: path.join(__dirname, '..', 'public', 'icon.png'),
  })

  if (isDev) {
    mainWindow.loadURL('http://localhost:5173')
    mainWindow.webContents.openDevTools()
  } else {
    mainWindow.loadFile(path.join(__dirname, '..', 'dist', 'index.html'))
  }

  mainWindow.on('closed', () => { mainWindow = null })
}

// ---------------------------------------------------------------------------
// IPC handlers
// ---------------------------------------------------------------------------

ipcMain.handle('open-file-dialog', async () => {
  const result = await dialog.showOpenDialog(mainWindow, {
    properties: ['openFile', 'multiSelections'],
    filters: [
      { name: 'Sysmon XML / EVTX', extensions: ['xml', 'evtx'] },
      { name: 'All Files',         extensions: ['*'] },
    ],
  })
  return result.canceled ? [] : result.filePaths
})

ipcMain.handle('open-external', (_, url) => shell.openExternal(url))

ipcMain.handle('get-backend-port', () => BACKEND_PORT)

// ---------------------------------------------------------------------------
// App lifecycle
// ---------------------------------------------------------------------------

app.whenReady().then(() => {
  startEngine()
  // Give Python 1.5 s to bind before opening the window
  setTimeout(createWindow, isDev ? 100 : 1500)
})

app.on('window-all-closed', () => {
  if (engineProcess) engineProcess.kill()
  if (process.platform !== 'darwin') app.quit()
})

app.on('before-quit', () => {
  if (engineProcess) engineProcess.kill()
})

app.on('activate', () => {
  if (mainWindow === null) createWindow()
})
