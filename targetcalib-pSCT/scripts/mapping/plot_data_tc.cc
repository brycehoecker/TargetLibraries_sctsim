/*
Plot data using TargetCalib and ROOT
Compile this script using the Makefile
*/
#include <sstream>
#include <fstream>
#include <iostream>
#include "TH2.h"
#include "TCanvas.h"
#include "TArrow.h"
#include "TText.h"
#include "TargetCalib/CameraConfiguration.h"

void plot(const char* fn="input_data.txt", const char* camera_version="1.0.1")
{

  auto camera_config = CTA::TargetCalib::CameraConfiguration(camera_version);
  auto m = camera_config.GetMapping();

  TH2F* h = new TH2F("h", "", 48, -0.5, 47.5, 48, -0.5, 47.5);

  std::ifstream infile(fn);
  if (!infile.is_open()) {
      std::cout << "Cannot find data file: " << fn << std::endl;
      return;
  }

  int pix = 0;
  float val;
  while (infile >> val){
    int x = m.GetColumn(pix);
    int y = m.GetRow(pix);
    h->SetBinContent(x,y,val);
    ++pix;
  }
  infile.close();

  TCanvas *c1 = new TCanvas("", "", 1200, 1200);
  h->Draw("colz");
  h->SetStats(0);

  int axl = m.fOTUpCol_l;
  int ayl = m.fOTUpRow_l;
  int axu = m.fOTUpCol_u;
  int ayu = m.fOTUpRow_u;
  TArrow* arr = new TArrow(axl, ayl, axu, ayu, 0.02);
  arr->SetLineColor(2);
  arr->SetFillColor(2);
  arr->Draw();
  TText *text = new TText();
  text -> SetTextColor(2);
  text -> SetTextSize(0.02);
  text -> SetTextAlign(21);
  text -> DrawText(axl, ayl , "ON-Telescope UP");
  c1->SaveAs("image_r_plot_data_tc.pdf");

}


int main(int argc, char** argv) {
  plot();
}