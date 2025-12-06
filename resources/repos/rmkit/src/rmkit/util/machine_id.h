#ifndef ____RMKIT__UTIL__MACHINE_ID_CPY_H
#define ____RMKIT__UTIL__MACHINE_ID_CPY_H
#include <iostream>
using namespace std;

#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <unistd.h>

#include "kobo_id.h"

namespace util {
  const int VERSION_MAX = 1024;
  enum RM_DEVICE_ID_E { UNKNOWN=0, RM1, RM2 };
  static char VERSION_STR[VERSION_MAX];
  static int RM_CUR_VERSION = -1;
  static int get_remarkable_version() {
    if (RM_CUR_VERSION == -1) {
      do { {
        RM_CUR_VERSION = UNKNOWN;
        auto fd = open("/sys/devices/soc0/machine", O_RDONLY);
        if (fd == -1) {
          std::cerr << "COULDNT OPEN machine id FILE" << ' ' << errno << std::endl;
          break; }

        int bytes = read(fd, VERSION_STR, VERSION_MAX);
        close(fd);
        if (bytes <= 0) {
          break; }

        VERSION_STR[bytes] = 0;
        auto version_str = string(VERSION_STR);
        while (version_str.size() > 0 && std::isspace(version_str.back())) {
          version_str.resize(version_str.size()-1); }

        if (version_str == string("reMarkable 1")) {
          RM_CUR_VERSION = RM1; }
        if (version_str == string("reMarkable 1.0")) {
          RM_CUR_VERSION = RM1; }
        if (version_str == string("reMarkable Prototype 1")) {
          RM_CUR_VERSION = RM1; }
        if (version_str == string("reMarkable 2.0")) {
          RM_CUR_VERSION = RM2; } }
      } while (false); }

    return RM_CUR_VERSION; }

  static int KOBO_CUR_VERSION = -1;
  static int get_kobo_version() {
    if (KOBO_CUR_VERSION == -1) {
      do { {
        KOBO_CUR_VERSION = UNKNOWN;
        auto fd = open("/mnt/onboard/.kobo/version", O_RDONLY);
        if (fd == -1) {
          std::cerr << "COULDNT OPEN KOBO VERSION FILE" << ' ' << errno << std::endl;
          break; }

        int bytes = read(fd, VERSION_STR, VERSION_MAX);
        close(fd);
        if (bytes <= 0) {
          break; }

        VERSION_STR[bytes] = 0;
        auto version_str = string(VERSION_STR);
        while (version_str.size() > 0 && std::isspace(version_str.back())) {
          version_str.resize(version_str.size()-1); }

        auto last_three = version_str.substr(version_str.size() - 3);
        KOBO_CUR_VERSION = atoi(last_three.c_str());

        switch (KOBO_CUR_VERSION) {
          case util::KOBO_DEVICE_ID_E::DEVICE_KOBO_CLARA_HD: {
            std::cerr << "RUNNING ON CLARA HD" << std::endl;
            break; }
          case util::KOBO_DEVICE_ID_E::DEVICE_KOBO_LIBRA_H2O: {
            std::cerr << "RUNNING ON LIBRA H2O" << std::endl;
            break; }
          case util::KOBO_DEVICE_ID_E::DEVICE_KOBO_ELIPSA_2E: {
            std::cerr << "RUNNING ON ELIPSA 2E" << std::endl;
            break; }
          default: {
            std::cerr << "*** UNRECOGNIZED KOBO DEVICE, TOUCH MAY NOT WORK ***" << std::endl;

            break; } } }
      } while (false); }

    return KOBO_CUR_VERSION; }; };


#endif