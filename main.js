// Modules to control application life and create native browser window
const {app, BrowserWindow} = require('electron')
const path = require('path')
require('electron-reload');
const spawn = require("child_process").spawn;
var ipc = require('electron').ipcMain;
const { dialog } = require('electron');

function createWindow () {
  // Create the browser window.
  const mainWindow = new BrowserWindow({
    width: 800,
    height: 600,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      nodeIntegration: true
    }
  })

  // and load the index.html of the app.
  mainWindow.loadFile('index.html')

  // Open the DevTools.
  mainWindow.webContents.openDevTools()
}

// This method will be called when Electron has finished
// initialization and is ready to create browser windows.
// Some APIs can only be used after this event occurs.
app.whenReady().then(createWindow)


// Quit when all windows are closed.
app.on('window-all-closed', function () {
  // On macOS it is common for applications and their menu bar
  // to stay active until the user quits explicitly with Cmd + Q
  if (process.platform !== 'darwin') app.quit()
})

app.on('activate', function () {
  // On macOS it's common to re-create a window in the app when the
  // dock icon is clicked and there are no other windows open.
  if (BrowserWindow.getAllWindows().length === 0) createWindow()
})


ipc.on('invokeAction', async function (event, data) {
  console.log('recieved action');
  console.log(data);
  const pythonProcess = spawn('python', data);
  pythonProcess.stdout.on('data', data => {
    const flag = data.toString().includes('There\'s conflicting values for label');
    if (flag) {
      var buttons = [];
      var offset = data.toString().includes('Select which value to use:') ? 2 : 3;
      const lines = data.toString().split('\n');
      for (var i = 0; i < lines.length - 3; i++) {
        buttons.push(i.toString());
      }
      dialog.showMessageBox({
        type: "none",
        buttons: buttons,
        title: 'Conflict from source',
        message: data.toString()
      }).then(res => {
        pythonProcess.stdin.write(`${res.response}\n`);
      })
    }
  });
  pythonProcess.stderr.on('data', data => {
    console.log('error: ', data.toString());
  });
});


// In this file you can include the rest of your app's specific main process
// code. You can also put them in separate files and require them here.
