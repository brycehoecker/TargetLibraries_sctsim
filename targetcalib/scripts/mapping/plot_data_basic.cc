/*
Plot data using only ROOT
Use this function interactively in root
*/
#include <sstream>
#include <fstream>
#include <iostream>
#include "TH2.h"
#include "TCanvas.h"
#include "TArrow.h"
#include "TText.h"

void get_row_col(int* row, int* col) {
  std::ifstream infile("full_camera_mapping.cfg");
  if (!infile.is_open()) {
      std::cout << "ERROR: Cannot find full_camera_mapping.cfg, "
          << "create with create_ascii.py" << std::endl;
      return;
  }
  char l[1024];
  infile.getline(l, 1024);

  int pix = 0;
  int pixel, slot, asic, ch, tmpix, r, c, sipmpix, sp, sp2;
  double xpix, ypix;

  while (infile >> pixel >> slot >> asic >> ch >> tmpix >> r >> c >> sipmpix
          >> sp >> sp2 >> xpix >> ypix){
    row[pix] = r;
    col[pix] = c;
    ++pix;
  }
  infile.close();
}

void plot(const char* fn="input_data.txt")
{
  int row[2048];
  int col[2048];
  get_row_col(row, col);

  TH2F* h = new TH2F("h", "", 48, -0.5, 47.5, 48, -0.5, 47.5);

  std::ifstream infile(fn);
  if (!infile.is_open()) {
      std::cout << "Cannot find data file: " << fn << std::endl;
      return;
  }

  int pix = 0;
  float val;
  while (infile >> val){
    int x = col[pix];
    int y = row[pix];
    std::cout << x << " " << y << " " << val << std::endl;
    h->SetBinContent(x,y,val);
    ++pix;
  }
  infile.close();

  h->Draw("colz");
  h->SetStats(0);

  int axl = 44;
  int ayl = 41;
  int axu = 44;
  int ayu = 46;
  TArrow* arr = new TArrow(axl, ayl, axu, ayu, 0.02);
  arr->SetLineColor(2);
  arr->SetFillColor(2);
  arr->Draw();
  TText *text = new TText();
  text -> SetTextColor(2);
  text -> SetTextSize(0.02);
  text -> SetTextAlign(22);
  text -> DrawText(axl, ayl , "ON-Telescope UP");

}
