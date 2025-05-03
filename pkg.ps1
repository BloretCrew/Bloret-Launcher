pyinstaller --onefile --noconsole --icon=bloret.ico --name=Bloret-Launcher `
--add-data "bloret.ico;." `
--add-data "config.json;." `
--add-data "ui;ui" `
--add-data "cmcl.json;." `
--add-data "cmcl.exe;." `
--add-data "cmcl.blank.json;." `
--add-data "restart.ps1;." `
--add-data "update.ps1;." `
--hidden-import=sip `
--hidden-import=qfluentwidgets `
--hidden-import=win11toast `
--paths=. `
Bloret-Launcher.py