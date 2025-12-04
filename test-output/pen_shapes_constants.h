/*
 * RM2 Coordinate Transformation Constants
 * Generated from empirical pen capture analysis
 * 
 * Coordinate System:
 *   Display: 1404×1872 portrait (X=left-right, Y=top-bottom, origin top-left)
 *   Wacom:   Rotated 90° and Y-inverted relative to display
 *   
 * Mapping:
 *   Display X (0-1404) → Wacom Y (90 to 15712)
 *   Display Y (0-1872) → Wacom X (20820 down to 211) [inverted]
 */

#ifndef RM2_COORD_H
#define RM2_COORD_H

// Display dimensions
#define DISPLAY_WIDTH   1404
#define DISPLAY_HEIGHT  1872

// Wacom hardware limits (from evtest)
#define WACOM_HW_X_MAX  20966
#define WACOM_HW_Y_MAX  15725

// Empirical usable bounds (from corner calibration)
#define WACOM_X_MIN     211
#define WACOM_X_MAX     20820
#define WACOM_Y_MIN     90
#define WACOM_Y_MAX     15712

// Calculated ranges
#define WACOM_X_RANGE   (WACOM_X_MAX - WACOM_X_MIN)  // 20609
#define WACOM_Y_RANGE   (WACOM_Y_MAX - WACOM_Y_MIN)  // 15622

// Pressure
#define PRESSURE_MAX    4095
#define PRESSURE_DEFAULT 2000

/*
 * Transform display coordinates to Wacom coordinates
 * 
 * display_x: 0 (left) to 1404 (right)
 * display_y: 0 (top) to 1872 (bottom)
 */
static inline int display_to_wacom_x(int display_x, int display_y) {
    // Display Y maps to Wacom X (inverted)
    return WACOM_X_MAX - (display_y * WACOM_X_RANGE / DISPLAY_HEIGHT);
}

static inline int display_to_wacom_y(int display_x, int display_y) {
    // Display X maps to Wacom Y
    return WACOM_Y_MIN + (display_x * WACOM_Y_RANGE / DISPLAY_WIDTH);
}

/*
 * Bounds checking
 */
static inline int clamp_wacom_x(int x) {
    if (x < WACOM_X_MIN) return WACOM_X_MIN;
    if (x > WACOM_X_MAX) return WACOM_X_MAX;
    return x;
}

static inline int clamp_wacom_y(int y) {
    if (y < WACOM_Y_MIN) return WACOM_Y_MIN;
    if (y > WACOM_Y_MAX) return WACOM_Y_MAX;
    return y;
}

#endif // RM2_COORD_H
