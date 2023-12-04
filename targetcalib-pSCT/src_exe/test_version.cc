//
// Created by Jason Watson on 25/10/2017.
//

#include <iostream>
#include <fstream>
#include <vector>
#include <unistd.h>
#include <set>
#include <algorithm>
#include <cassert>

#include "TargetCalib/CameraConfiguration.h"

using namespace CTA::TargetCalib;

void ShowUsage(char *s);

int main(int argc, char **argv) {
  assert(Version("3.7.8") == Version("3.7.8"));
  assert(Version("3.7.8") == Version("3.7.8"));
  assert(!(Version("3.7.8") < Version("3.7.8")));
  assert(!(Version("3.7.9") < Version("3.7.8")));
  assert(Version("3") < Version("3.7.9"));
  assert(Version("1.7.9") < Version("3.1"));
  assert("3.1" <= Version("3.1.4"));



  std::cout << "Printing version (3.7.8): " << Version("3.7.8") << std::endl;
  return 0;
}