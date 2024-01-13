// Copyright (c) 2015 The CTA Consortium. All rights reserved.
#include <TargetDriver/RegisterSettings.h>
#include <iostream>
using namespace std;
int main(int argc, char** argv) {
  if (argc != 5) {
    cout << "Usage: <FPGA.def> <ASIC.def> <OutputFPGA.md> <OutputASIC.md>"
         << endl;
    return 0;
  }
  CTA::TargetDriver::RegisterSettings ts(argv[1], argv[2]);
  ts.GenerateFPGAMarkdown(argv[3]);
  ts.GenerateASICMarkdown(argv[4]);

  return 0;
}
