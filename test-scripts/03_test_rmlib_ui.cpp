/*
 * Test 3: rMlib UI Framework Test
 *
 * Tests if rMlib can create a simple overlay UI without rm2fb
 * Based on rM2-stuff/tools/ui-tests
 *
 * Compile: (see build instructions below)
 * Run: ./test_rmlib_ui
 */

#include <iostream>
#include <unistd.h>

#include <Canvas.h>
#include <FrameBuffer.h>
#include <Input.h>
#include <UI.h>

using namespace rmlib;

// Simple button that shows "Test Overlay"
class TestOverlay : public StatelessWidget<TestOverlay> {
public:
    auto build(AppContext& /*unused*/, const BuildContext& /*unused*/) const {
        return Center(
            Column(
                Text("🔧 Test Overlay Running"),
                Text("Tap anywhere to exit"),
                Button("Close", []() {
                    std::cout << "Button clicked!\n";
                    exit(0);
                })
            )
        );
    }
};

// Drawing test - shows if we can draw without affecting xochitl
class SimpleDrawer : public StatelessWidget<SimpleDrawer> {
public:
    auto build(AppContext& /*unused*/, const BuildContext& /*unused*/) const {
        return GestureDetector(
            Container(
                Text("Draw Test - Tap to mark"),
                Insets::all(20)
            ),
            Gestures{}.onTap([this]() {
                std::cout << "Tap detected\n";
            })
        );
    }
};

int main() {
    std::cout << "Test 3: rMlib UI Framework\n";
    std::cout << "===========================\n\n";

    std::cout << "Attempting to create UI overlay...\n";

    // Try to run app
    auto optErr = runApp(TestOverlay());

    if (!optErr.has_value()) {
        std::cerr << "❌ Error: " << optErr.error().msg << "\n";
        std::cerr << "\nThis error is expected if:\n";
        std::cerr << "  - rm2fb is not running (not supported on 3.24)\n";
        std::cerr << "  - Device is not reMarkable 2\n";
        std::cerr << "  - Missing dependencies\n";
        return EXIT_FAILURE;
    }

    std::cout << "✓ UI framework initialized!\n";
    return EXIT_SUCCESS;
}

/*
 * BUILD INSTRUCTIONS:
 *
 * This requires the rM2-stuff toolchain. To build:
 *
 * 1. Set up cross-compilation environment:
 *    cd resources/repos/rM2-stuff
 *    mkdir -p build && cd build
 *    cmake .. -DCMAKE_TOOLCHAIN_FILE=../cmake/toolchain.cmake
 *
 * 2. Build rMlib:
 *    make rMlib
 *
 * 3. Compile this test:
 *    arm-remarkable-linux-gnueabihf-g++ \
 *      -o test_rmlib_ui \
 *      ../../../test-scripts/03_test_rmlib_ui.cpp \
 *      -I../libs/rMlib/include \
 *      -L. \
 *      -lrMlib \
 *      -std=c++17
 *
 * 4. Deploy to device:
 *    scp test_rmlib_ui root@10.11.99.1:/home/root/
 *
 * 5. Run on device:
 *    ssh root@10.11.99.1
 *    ./test_rmlib_ui
 */
