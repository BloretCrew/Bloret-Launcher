// mainwindow.h
#include <QMainWindow>
#include <QThread>
#include <QSettings>
#include <QNetworkAccessManager>
#include <QJsonObject>
#include <QJsonDocument>
#include <QFile>
#include <QDir>
#include <QMessageBox>
#include <QTimer>
#include <QProcess>
#include <QDesktopServices>
#include <QPalette>
#include <QIcon>
#include <QMovie>
#include <QPixmap>
#include <QSharedPointer>
#include <QCryptographicHash>
#include <QStandardPaths>
#include <QFile>
#include <QTextStream>
#include <QJsonParseError>
#include <QJsonArray>
#include <QJsonObject>
#include <QJsonDocument>

class DownloadWorker : public QThread {
    Q_OBJECT
public:
    void run() override {
        // 模拟数据处理
        sleep(5);
        emit finished();
    }
signals:
    void finished();
};

class RunScriptThread : public QThread {
    Q_OBJECT
public:
    RunScriptThread(QObject* parent = nullptr) : QThread(parent) {}
    void run() override {
        QString scriptPath = "run.ps1";
        QProcess process;
        process.start("powershell", {"-ExecutionPolicy", "Bypass", "-File", scriptPath});
        process.waitForFinished(-1);

        if (process.exitCode() == 0) {
            emit finished();
        } else {
            emit errorOccurred(process.readAllStandardError());
        }
    }
signals:
    void finished();
    void errorOccurred(const QString& error);
};

class LoadMinecraftVersionsThread : public QThread {
    Q_OBJECT
    QString versionType;
public:
    LoadMinecraftVersionsThread(const QString& type, QObject* parent = nullptr) 
        : QThread(parent), versionType(type) {}
    void run() override {
        QNetworkAccessManager manager;
        QNetworkReply* reply = manager.get(QNetworkRequest(QUrl("https://bmclapi2.bangbang93.com/mc/game/version_manifest.json")));
        QEventLoop loop;
        connect(reply, &QNetworkReply::finished, &loop, &QEventLoop::quit);
        loop.exec();

        if (reply->error() == QNetworkReply::NoError) {
            QByteArray data = reply->readAll();
            QJsonDocument doc = QJsonDocument::fromJson(data);
            QJsonObject obj = doc.object();
            QJsonArray versions = obj["versions"].toArray();

            QStringList verIdMain, verIdShort, verIdLong;
            for (const QJsonValue& val : versions) {
                QJsonObject ver = val.toObject();
                QString type = ver["type"].toString();
                if (type != "snapshot" && type != "old_alpha" && type != "old_beta") {
                    verIdMain << ver["id"].toString();
                } else {
                    if (type == "snapshot") {
                        verIdShort << ver["id"].toString();
                    } else if (type == "old_alpha" || type == "old_beta") {
                        verIdLong << ver["id"].toString();
                    }
                }
            }

            QStringList result;
            if (versionType == "百络谷支持版本") {
                result = {"1.21.4", "1.21.3", "1.21.2", "1.21.1", "1.21"};
            } else if (versionType == "正式版本") {
                result = verIdMain;
            } else if (versionType == "快照版本") {
                result = verIdShort;
            } else if (versionType == "远古版本") {
                result = verIdLong;
            }
            emit versionsLoaded(result);
        } else {
            emit errorOccurred("请求错误");
        }
    }
signals:
    void versionsLoaded(const QStringList&);
    void errorOccurred(const QString&);
};

class MainWindow : public QMainWindow {
    Q_OBJECT
public:
    MainWindow();
private:
    QSettings* settings;
    QNetworkAccessManager* networkManager;
    QJsonObject cmclData;
    QString playerUuid;
    QString playerName;
    QString loginMod;
    QStringList setList;
    bool isRunning;
    QTimer* logTimer;
    void initLogging();
    void loadCmclData();
    void setupNavigation();
    void updateVersionComboBox();
    void showInfoBar(const QString& title, const QString& content, QMessageLogger::Severity level);
private slots:
    void onDownloadFinished();
    void onDownloadError(const QString& error);
    void onShowWayChanged(const QString& versionType);
    void onDownloadClicked();
    void onLoginFinished(bool success, const QString& message);
};