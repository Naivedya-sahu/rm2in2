#ifndef ____RMKIT__INPUT__DEVICE_ID_CPY_H
#define ____RMKIT__INPUT__DEVICE_ID_CPY_H
#include <linux/input.h>
#include <sys/ioctl.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <unistd.h>
#include <string>



#define BITS_PER_LONG (sizeof(long) * 8)
#define NBITS(x) ((((x)-1)/BITS_PER_LONG)+1)
#define OFF(x)  ((x)%BITS_PER_LONG)
#define BIT(x)  (1UL<<OFF(x))
#define LONG(x) ((x)/BITS_PER_LONG)
#define test_bit(bit, array)    ((array[LONG(bit)] >> OFF(bit)) & 1)












namespace input {
  enum EV_TYPE { TOUCH, STYLUS, BUTTONS, UNKNOWN, INVALID };
  static bool check_bit_set(int fd, int type, int i) {
    unsigned long bit[NBITS(KEY_MAX)];
    ioctl(fd, EVIOCGBIT(type, KEY_MAX), bit);
    return test_bit(i, bit); }


  static EV_TYPE id_by_capabilities(int fd) {
    int version;

    if (ioctl(fd, EVIOCGVERSION, &version)) {
      return INVALID; }

    unsigned long bit[EV_MAX];
    ioctl(fd, EVIOCGBIT(0, EV_MAX), bit);

    if (check_bit_set(fd, EV_ABS, ABS_MT_TRACKING_ID)) {
      return TOUCH; }

    if (test_bit(EV_KEY, bit)) {
      if (check_bit_set(fd, EV_KEY, BTN_STYLUS) && test_bit(EV_ABS, bit)) {
        return STYLUS; }
      if (check_bit_set(fd, EV_KEY, KEY_POWER)) {
        return BUTTONS; } }

    if (check_bit_set(fd, EV_KEY, BTN_TOOL_PEN)) {
      return TOUCH; }

    return UNKNOWN; }

  static bool supports_stylus(int fd) {
    if (fd <= 0) {
      return false; }

    unsigned long bit[EV_MAX];
    ioctl(fd, EVIOCGBIT(0, EV_MAX), bit);
    if (check_bit_set(fd, EV_KEY, BTN_STYLUS) && test_bit(EV_ABS, bit)) {
      return true; }

    return false; }

  static EV_TYPE id_by_name(int fd) {
    char name[256];
    ioctl(fd, EVIOCGNAME(sizeof(name)), name);
    auto s = std::string(name);
    if (s.find("I2C Digitizer") != -1) {
      return STYLUS; }
    if (s.find("_mt") != -1) {
      return TOUCH; }
    if (s.find("keys") != -1) {
      return BUTTONS; }

    return UNKNOWN; }; };

#endif