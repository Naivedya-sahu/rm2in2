/*
 * RM2 Coordinate Transformation Constants
 * Generated from empirical pen capture analysis
 */

#ifndef RM2_COORD_H
#define RM2_COORD_H

// Display dimensions
#define DISPLAY_WIDTH   1404
#define DISPLAY_HEIGHT  1872

// Wacom hardware limits
#define WACOM_HW_X_MAX  20966
#define WACOM_HW_Y_MAX  15725

// Empirical usable bounds
#define WACOM_X_MIN     211
#define WACOM_X_MAX     20820
#define WACOM_Y_MIN     90
#define WACOM_Y_MAX     15712

#define WACOM_X_RANGE   (WACOM_X_MAX - WACOM_X_MIN)
#define WACOM_Y_RANGE   (WACOM_Y_MAX - WACOM_Y_MIN)

#define PRESSURE_MAX    4095
#define PRESSURE_DEFAULT 2000

/*
 * Transform display coordinates to Wacom coordinates
 */
static inline int display_to_wacom_x(int display_y) {
    return WACOM_X_MAX - (display_y * WACOM_X_RANGE / DISPLAY_HEIGHT);
}

static inline int display_to_wacom_y(int display_x) {
    return WACOM_Y_MIN + (display_x * WACOM_Y_RANGE / DISPLAY_WIDTH);
}

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

#endif
