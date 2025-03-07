// mainwindow.cpp
#include "mainwindow.h"

MainWindow::MainWindow() {
    settings = new QSettings("Bloret", "Launcher");
    networkManager = new QNetworkAccessManager(this);
    isRunning = false;
    logTimer = new QTimer(this);
    logTimer->setInterval(1000);
    initLogging();
    loadCmclData();
    setupNavigation();
}

void MainWindow::initLogging() {
    QDir logDir("log");
    if (!logDir.exists()) logDir.mkpath(".");
    QString logFile = logDir.absoluteFilePath(
        QDate::currentDate().toString("yyyyMMdd_hhmmss") + ".log"
    );
    QFile file(logFile);
    if (!file.open(QIODevice::WriteOnly | QIODevice::Append)) {
        qDebug() << "Failed to open log file";
        return;
    }
    QTextStream out(&file);
    out << "Starting application\n";
}

void MainWindow::loadCmclData() {
    QFile cmclFile("cmcl.json");
    if (cmclFile.open(QIODevice::ReadOnly)) {
        QByteArray data = cmclFile.readAll();
        QJsonParseError error;
        QJsonDocument doc = QJsonDocument::fromJson(data, &error);
        if (!error.error) {
            cmclData = doc.object();
            const QJsonArray& accounts = cmclData["accounts"].toArray();
            if (!accounts.isEmpty()) {
                const QJsonObject& account = accounts[0].toObject();
                playerName = account["playerName"].toString("未登录");
                int loginMethod = account["loginMethod"].toInt(-1);
                loginMod = loginMethod == 0 ? "离线登录" : (loginMethod == 2 ? "微软登录" : "未知");
            }
        }
    }
}

void MainWindow::setupNavigation() {
    // 初始化导航栏和各个页面的布局
    // 这部分需要根据具体UI设计实现
}

void MainWindow::onShowWayChanged(const QString& versionType) {
    LoadMinecraftVersionsThread* thread = new LoadMinecraftVersionsThread(versionType);
    connect(thread, &LoadMinecraftVersionsThread::versionsLoaded, [this](const QStringList& versions) {
        // 更新版本下拉框
        updateVersionComboBox();
    });
    thread->start();
}

void MainWindow::updateVersionComboBox() {
    // 更新版本选择框的逻辑
}

void MainWindow::onDownloadClicked() {
    // 下载逻辑实现
}

void MainWindow::onDownloadFinished() {
    showInfoBar("下载完成", "版本已成功下载", QtInfoMsg);
}

void MainWindow::onDownloadError(const QString& error) {
    showInfoBar("下载失败", error, QtWarningMsg);
}

void MainWindow::showInfoBar(const QString& title, const QString& content, QMessageLogger::Severity level) {
    // 实现信息提示框的显示逻辑
}