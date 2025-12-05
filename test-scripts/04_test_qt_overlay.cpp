/*
 * Test 4: Qt Overlay Window
 *
 * Tests if we can create a Qt window that overlays on xochitl
 * Uses system Qt5 libraries (no rm2fb needed)
 *
 * This should work independently of rm2fb since Qt has its own
 * display backend on the reMarkable.
 *
 * Compile: (see build instructions below)
 * Run: ./test_qt_overlay
 */

#include <QApplication>
#include <QWidget>
#include <QPushButton>
#include <QVBoxLayout>
#include <QLabel>
#include <QProcess>
#include <QDebug>

class TestOverlay : public QWidget {
    Q_OBJECT

public:
    TestOverlay(QWidget *parent = nullptr) : QWidget(parent) {
        setupUI();
    }

private:
    void setupUI() {
        // Make window frameless and stay on top
        setWindowFlags(Qt::FramelessWindowHint | Qt::WindowStaysOnTopHint);

        // Semi-transparent background
        setStyleSheet("background-color: rgba(255, 255, 255, 200);");

        QVBoxLayout *layout = new QVBoxLayout(this);

        QLabel *title = new QLabel("🔧 Qt Overlay Test", this);
        title->setStyleSheet("font-size: 24px; font-weight: bold;");
        layout->addWidget(title);

        QLabel *info = new QLabel(
            "If you see this overlay,\n"
            "Qt rendering works without rm2fb!",
            this
        );
        layout->addWidget(info);

        QPushButton *lampTest = new QPushButton("Test lamp Integration", this);
        connect(lampTest, &QPushButton::clicked, this, &TestOverlay::testLamp);
        layout->addWidget(lampTest);

        QPushButton *closeBtn = new QPushButton("Close", this);
        connect(closeBtn, &QPushButton::clicked, this, &QWidget::close);
        layout->addWidget(closeBtn);

        setLayout(layout);

        // Position in top-right corner
        setGeometry(900, 50, 450, 200);
    }

private slots:
    void testLamp() {
        qDebug() << "Testing lamp integration...";

        QProcess lamp;
        lamp.start("lamp");
        if (!lamp.waitForStarted()) {
            qDebug() << "❌ Failed to start lamp";
            return;
        }

        // Send test commands to lamp
        QString commands =
            "pen rectangle 200 200 600 400\n"
            "pen circle 400 300 50 50\n";

        lamp.write(commands.toUtf8());
        lamp.closeWriteChannel();
        lamp.waitForFinished();

        qDebug() << "✓ Lamp commands sent";
    }
};

int main(int argc, char *argv[]) {
    qDebug() << "Test 4: Qt Overlay Window";
    qDebug() << "==========================\n";

    QApplication app(argc, argv);

    qDebug() << "Qt Version:" << qVersion();
    qDebug() << "Creating overlay widget...\n";

    TestOverlay overlay;
    overlay.show();

    qDebug() << "✓ Overlay displayed!";
    qDebug() << "If you see the overlay window, Qt rendering works.";

    return app.exec();
}

#include "04_test_qt_overlay.moc"

/*
 * BUILD INSTRUCTIONS:
 *
 * Option A: Using reMarkable toolchain
 *
 * 1. Set up Qt cross-compilation:
 *    export PATH=/path/to/remarkable-toolchain/bin:$PATH
 *    export QT_SELECT=remarkable
 *
 * 2. Create .pro file:
 *    cat > test_qt.pro << 'EOF'
 *    QT += core gui widgets
 *    TARGET = test_qt_overlay
 *    SOURCES += 04_test_qt_overlay.cpp
 *    EOF
 *
 * 3. Build:
 *    qmake-remarkable test_qt.pro
 *    make
 *
 * 4. Deploy:
 *    scp test_qt_overlay root@10.11.99.1:/home/root/
 *
 * Option B: Direct compilation (if Qt5 dev tools available)
 *
 *    arm-remarkable-linux-gnueabihf-g++ \
 *      -o test_qt_overlay \
 *      04_test_qt_overlay.cpp \
 *      $(pkg-config --cflags --libs Qt5Widgets) \
 *      -fPIC
 *
 * RUNNING:
 *
 * On device:
 *    export LD_LIBRARY_PATH=/usr/lib:$LD_LIBRARY_PATH
 *    export QT_QPA_PLATFORM=eglfs
 *    ./test_qt_overlay
 *
 * If it conflicts with xochitl, try:
 *    systemctl stop xochitl
 *    ./test_qt_overlay
 *    systemctl start xochitl
 */
