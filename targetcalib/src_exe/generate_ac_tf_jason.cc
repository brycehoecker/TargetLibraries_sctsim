/*
documentation

author: david.jankowsky@fau.de
*/

#include <vector>
#include <iostream>
#include <numeric>
#include <math.h>
#include <time.h>
#include <thread>
#include <algorithm>
#include <fstream>

// Target
#include "TargetDriver/DataPacket.h"
#include "TargetDriver/Waveform.h"
#include "TargetIO/EventFileReader.h"
#include "TargetCalib/TfMaker.h"

// Root
#include <TH1F.h>
#include <TH2F.h>
#include <TH1I.h>
#include <TF1.h>
#include <TGraph.h>
#include <TFile.h>
#include <TROOT.h>
#include <TStyle.h>
#include <TCanvas.h>
#include <TApplication.h>
#include <TLine.h>

// uncomment to create TargetCalib TF file
#define Use_TFmaker

using namespace CTA::TargetDriver;
using namespace CTA::TargetIO;
using namespace CTA::TargetCalib;
using namespace std;

// Some constant values
const uint16_t CELLS         = 4096;
const uint16_t CHANNELS      = 16;
const uint16_t ASICS         = 4;
const uint16_t MAX_VPED      = 3000;
const uint16_t NBLOCKS       = 3; 
const float PEAKPOS          = 45.00; // approximate peak position as set by trigger delay
const uint16_t MODULE_ID     = 0;
const uint16_t NMODULES      = 1;
//position tests
const uint16_t NR_FITS       = 300; // nr of fits to determine pulse position

// module id related strings and paths
std::string ModuleID = "SN0074";
std::string FilePrefix = "/Volumes/gct-jason/data_checs/tf/ac_tf_tm" + ModuleID + "/Amplitude_";
std::string OutDir = ModuleID + "/";
std::string OutFile = OutDir + "TF_File_" + ModuleID + ".tcal";
std::string dir = OutDir + "plots/"; 

// functions
int GetArrayPos(uint16_t asic, uint16_t channel, uint16_t array[][CHANNELS], uint16_t size);


// main program
int main() {
  
  // Create TFile to store some diagnostic data
  std::string tfile1_name = OutDir + "ac_plots_" + ModuleID + ".root";
  TFile *tfile = new TFile(tfile1_name.c_str(), "RECREATE");

  // time order of chans of every asic
  // used for interpolation between neighboring channels (if fit didnt work)
  uint16_t time_order[4][16] =
    {{9, 3, 2, 1, 12, 4, 7, 11, 15, 0, 14, 13, 6, 8, 5, 10},
    {5, 7, 10, 9, 3, 4, 2, 8, 6, 0, 1, 15, 12, 11, 13, 14},
    {6, 3, 13, 12, 5, 2, 14, 0, 11, 15, 7, 9, 8, 4, 1, 10},
    {10, 9, 11, 8, 12, 7, 0, 2, 5, 4, 1, 13, 6, 3, 14, 15}};

  // Build up Vector of all vped
  // by looking at all taken files
  vector<int16_t> vped;
  // give negative values by hand
  /*
  vped.push_back(-180); // -180 at 1752
  vped.push_back(-150); // -150 at 1496
  vped.push_back(-110); // -110 at 1048
  vped.push_back(-70); // -70 at 600
  vped.push_back(-40); // -39 at 280
  vped.push_back(-30); // -29 at 200
  vped.push_back(-18); // -18 at 112
  vped.push_back(-10); // -10 at 48
  */
  // values determined by direct measurement
  // with fit a*x+b
  /*
  vped.push_back(-361); // -361 at 1752
  vped.push_back(-309); // -309 at 1496
  vped.push_back(-218); // -218 at 1048
  vped.push_back(-126); // -126 at 600
  vped.push_back(-61); // -61 at 280
  vped.push_back(-45); // -45 at 200
  vped.push_back(-27); // -27 at 112
  vped.push_back(-14); // -14 at 48
  */
  // values determined by direct measurement
  // with fit a*x
  vped.push_back(-363); // -361 at 1752
  vped.push_back(-310); // -309 at 1496
  vped.push_back(-217); // -218 at 1048
  vped.push_back(-124); // -126 at 600
  vped.push_back(-58); // -61 at 280
  vped.push_back(-41); // -45 at 200
  vped.push_back(-23); // -27 at 112
  vped.push_back(-10); // -14 at 48
  // remark: correct also bins at end of script
  uint16_t NegValues = vped.size();

  // create array of files
  uint16_t NFiles = 0;
  for(int i = 0; i < MAX_VPED+1; i++){
    std::string InFile  = FilePrefix + Form("%d",i) + "_r1.tio"; //  Define Filename of read in EventFile
    if (!std::ifstream(InFile)) {
      continue;
    }
     else{
       vped.push_back(i);
     }
    NFiles++;
  }
  std::cout << "Found "<< NFiles << " Files\n" << std::endl;
  std::cout << "Vped vector has "<<vped.size()<<" entries" <<std::endl;
  for(uint16_t i = 0;i<vped.size();i++){
    std::cout<<"Vped index "<< i <<" Vped Value "<< vped[i] << std::endl;
  }
  std::cout << std::endl;

  // create some general variables
  uint8_t* data;
  DataPacket prec;//  Datapacket is accesible via prec
  uint16_t ColID, RowID, PhaseID, StartingBlock, NSamples, FirstCellId; // Define important integers
  float Offset, Scale;

  float PeakADC_stdev[ASICS][CHANNELS][CELLS][vped.size()];
  std::fill(&PeakADC_stdev[0][0][0][0], &PeakADC_stdev[0][0][0][0] + sizeof(PeakADC_stdev) / sizeof(PeakADC_stdev[0][0][0][0]), 0);
  float PeakADC_mean[ASICS][CHANNELS][CELLS][vped.size()];
  std::fill(&PeakADC_mean[0][0][0][0], &PeakADC_mean[0][0][0][0] + sizeof(PeakADC_mean) / sizeof(PeakADC_mean[0][0][0][0]), 0);

  // Create variables & histograms for peak & min pos search
  float PeakPositions[vped.size()][ASICS][CHANNELS];
  uint16_t MinPositions[vped.size()][ASICS][CHANNELS];  

  // vector to array since root needs arrays for the plots
  float vped_arr[vped.size()];
  for(uint16_t i=0; i<vped.size(); ++i){
    vped_arr[i] = vped[i];
  }

  // Determine peak positions for certain amplitudes
  // this range corresponds usually to roughly 50 to 1800 mV amplitudes
  for(uint16_t vpeds = 10 + NegValues; vpeds < 54 + NegValues; ++vpeds){
    // search for peak positions
    std::cout << "Searching for peak positions" << std::endl;
    std::cout << "Using vped value " << vped[vpeds] << std::endl;
    std::string InFile  = FilePrefix + Form("%d",vped[vpeds]) + "_r1.tio";
    std::cout << "Reading file: " << InFile << std::endl;
    // reading file and getting calibration information
    EventFileReader reader(InFile.c_str());                     //  Open up the EventFile
    uint32_t packetsize = reader.GetPacketSize();               //  Get packet size of stored packets
    int NEvents         = reader.GetNEvents();                  //  Get number of stored events
    std::cout << "Using " << NR_FITS << " events of " << NEvents << " for calculations" << std::endl;
    bool R1 = false;
    if (reader.HasCardImage("R1")) {
      R1 = reader.GetCardImage("R1")->GetValue()->AsBool();
      if (R1) {
        Offset = (float) reader.GetCardImage("OFFSET")->GetValue()->AsDouble();
        Scale = (float) reader.GetCardImage("SCALE")->GetValue()->AsDouble();
      }
    }
    // create histograms to store acquired peak & min positions
    TH1F *hPeakPos[ASICS][CHANNELS];
    TH1F *hMinPos[ASICS][CHANNELS];
    char pos_name[50];
    for(int asics = 0; asics<ASICS; ++asics){
      for(int channels = 0; channels<CHANNELS; ++channels){
        sprintf(pos_name, "PeakPos_Vped%d_Asic%d_Chan%d", vped[vpeds], asics, channels);
        hPeakPos[asics][channels] = new TH1F(pos_name, pos_name,NBLOCKS*32*100,0,NBLOCKS*32);
        sprintf(pos_name, "MinPos_Vped%d_Asic%d_Chan%d", vped[vpeds], asics, channels);
        hMinPos[asics][channels] = new TH1F(pos_name, pos_name,NBLOCKS*32*100,0,NBLOCKS*32);        
      }
    }

    bool PeakGoodFit = true; // variable to store goodness of fit
    // loop: asics, channels, events
    for(int asics = 0; asics<ASICS; ++asics){
      for(int channels = 0; channels<CHANNELS; ++channels){
        for(int evts = 0; evts<NR_FITS; ++evts){
          if(evts%1000 == 0) std::cout << asics*CHANNELS*NR_FITS + channels*NR_FITS + evts << " of " << ASICS*CHANNELS*NR_FITS << "\r" << std::flush;
          
          data          = reader.GetEventPacket(evts,asics);
          prec.Assign(data, packetsize);
          if(!prec.IsValid()) continue; // validate packet

          // get information from packet
          ColID         = prec.GetColumn();
          RowID         = prec.GetRow();
          PhaseID       = prec.GetBlockPhase();
          StartingBlock = RowID+ColID*8;
          FirstCellId   = prec.GetFirstCellId();

          Waveform* w = prec.GetWaveform(channels);         // Get waveform from packet
          NSamples = w->GetSamples();                       // Get the number of Samples in Waveform (should be constant)

          // create histogram to store waveform for peak position determination
          char histname1[100];
          sprintf(histname1, "Vped%d_Asic%d_Channel%d_Event%d", vped[vpeds], asics, channels, evts);
          TH1I* hist1 = new TH1I(histname1,histname1,NSamples,0.,NSamples);  //  Histogram for each Waveform
          PeakGoodFit = true;
          float value_calib1 = 0 , value_calib2 = 0, value_calib3 = 0;
          // read out the waveform
          for(int sample = 0; sample < NSamples; sample++){
            float value_calib = ((float) w->GetADC16bit(sample) / Scale) - Offset;
            hist1->SetBinContent(sample+1, value_calib);  // Set new Bin content (BinNR starts from 1)
            // quality check: skip event if overflow or too large adc values occured
            // since this might disturb the fitting process
            if( (value_calib1 > 500 && value_calib2 < 1) || (value_calib3 > 500 && value_calib2 < 1) || value_calib > 4000)
            {
              PeakGoodFit = false;
            }
            // variables to store more samples for overflow checks
            value_calib3 = value_calib2;
            value_calib2 = value_calib1;
            value_calib1 = value_calib;
          }
          // if there were already problems: skip event
          if( !PeakGoodFit ){
            delete hist1;
            delete w;
            continue;
          }

          // create fit functions: landau+landau
          // do a prefit to get better starting values for the real fit
          TF1* ll_prefit = new TF1("ll_prefit","landau+landau(3)",0,NBLOCKS*32);
          ll_prefit->SetParameter(0,vped[vpeds]*11.0);
          ll_prefit->SetParameter(1,PEAKPOS);
          ll_prefit->SetParameter(2,3.0);
          ll_prefit->SetParameter(3,vped[vpeds]*(-2.75));
          ll_prefit->SetParameter(4,PEAKPOS+21);
          ll_prefit->SetParameter(5,6.5);
          hist1->Fit("ll_prefit","WWQR");

          //  Quality Controll stage 1: When Fit is not good move on!
          if ( ll_prefit->GetParameter(1) < 40 || ll_prefit->GetParameter(1) > 65
              || ll_prefit->GetMaximumX() < 40 || ll_prefit->GetMaximumX() > 65
              || ll_prefit->GetParameter(2) > 10
              || ll_prefit->GetMinimumX() < 50 || ll_prefit->GetMinimumX() > 90
              || ll_prefit->GetParameter(5) > 20 )
          {
            delete hist1;
            delete w;
            delete ll_prefit;
            continue;
          }

          // second fit to improve results
          TF1* llfit = new TF1("llfit","landau+landau(3)",0,NBLOCKS*32);
          llfit->SetParameter(0,ll_prefit->GetParameter(0));
          llfit->SetParameter(1,ll_prefit->GetParameter(1));
          llfit->SetParameter(2,ll_prefit->GetParameter(2));
          llfit->SetParameter(3,ll_prefit->GetParameter(3));
          llfit->SetParameter(4,ll_prefit->GetParameter(4));
          llfit->SetParameter(5,ll_prefit->GetParameter(5));
          hist1->Fit("llfit","WWQR");

          //  Quality Controll stage 2: When Fit is not good move on!
          if ( llfit->GetParameter(1) < 40 || llfit->GetParameter(1) > 65
              || llfit->GetMaximumX() < 40 || llfit->GetMaximumX() > 65
              || llfit->GetParameter(2) > 10
              || llfit->GetMinimumX() < 50 || llfit->GetMinimumX() > 90
              || llfit->GetParameter(5) > 20 )
          {
            delete hist1;
            delete w;
            delete ll_prefit;
            delete llfit;
            continue;
          }

          // Fill histograms with determined peak positions
          hPeakPos[asics][channels]->Fill(llfit->GetMaximumX());
          hMinPos[asics][channels]->Fill(llfit->GetMinimumX());
          
          delete hist1;
          delete w;
          delete ll_prefit;
          delete llfit;
        }
      }
    }
    std::cout << "\n" << std::endl;
    std::cout << "Finished determination of peak positions" << std::endl;

    // Save determined peak pos in array for further use
    // TODO: make fallback options fail proof
    for(int asics = 0; asics<ASICS; ++asics){
      for(int channels = 0; channels<CHANNELS; ++channels){
        // alternative approach if not enough fits were possible
        // interpolate peak position with neighbouring channels
        // Peak positions:
        if(hPeakPos[asics][channels]->GetEntries() < 15){
          // do the correction if there were not enough fits possible
          int array_pos = GetArrayPos(asics, channels, time_order, CHANNELS);
          int chan1 = 0;
          int chan2 = 0;
          if( array_pos == 0){
            chan2 = time_order[asics][array_pos+1];
            PeakPositions[vpeds][asics][channels] = hPeakPos[asics][chan2]->GetMean();
          }
          else if( array_pos == 15){
            chan1 = time_order[asics][array_pos-1];
            PeakPositions[vpeds][asics][channels] = hPeakPos[asics][chan1]->GetMean();
          }
          else{
            chan1 = time_order[asics][array_pos-1];
            chan2 = time_order[asics][array_pos+1];
            if(hPeakPos[asics][chan1]->GetMean() < 10 || hPeakPos[asics][chan2]->GetMean() < 10){
              for(int i=2; i<5; ++i){
                if(hPeakPos[asics][chan1]->GetMean() < 10) chan1 = time_order[asics][array_pos-i];
                if(hPeakPos[asics][chan2]->GetMean() < 10) chan2 = time_order[asics][array_pos+i];
                if(hPeakPos[asics][chan1]->GetMean() > 10 && hPeakPos[asics][chan2]->GetMean() > 10) continue;
              }
            }
            PeakPositions[vpeds][asics][channels] = abs((hPeakPos[asics][chan1]->GetMean() + hPeakPos[asics][chan2]->GetMean())/2.0);
          }
        }
        // if fitting worked: use mean value of the fits
        // (normal approach)
        else{
          PeakPositions[vpeds][asics][channels] = hPeakPos[asics][channels]->GetMean();
        }
        // correction if Peak Post fits did not work
        // -> take value from previous amplitude
        for(int i=1; i<5; ++i){
          if(PeakPositions[vpeds][asics][channels] < 10){
            PeakPositions[vpeds][asics][channels] = PeakPositions[vpeds-i][asics][channels];
          }
          if(PeakPositions[vpeds][asics][channels] > 10) continue;
        }                
        // do the same for negative values (minimum positions)
        if(hMinPos[asics][channels]->GetEntries() < 15){
          // do the correction if there were not enough fits possible
          int array_pos = GetArrayPos(asics, channels, time_order, CHANNELS);
          int chan1 = 0;
          int chan2 = 0;
          if( array_pos == 0){
            chan2 = time_order[asics][array_pos+1];
            MinPositions[vpeds][asics][channels] = int(hMinPos[asics][chan2]->GetMean());
          }
          else if( array_pos == 15){
            chan1 = time_order[asics][array_pos-1];
            MinPositions[vpeds][asics][channels] = int(hMinPos[asics][chan1]->GetMean());
          }
          else{
            chan1 = time_order[asics][array_pos-1];
            chan2 = time_order[asics][array_pos+1];
            MinPositions[vpeds][asics][channels] = int(abs((hMinPos[asics][chan1]->GetMean() + hMinPos[asics][chan2]->GetMean())/2.0));
          }
        }
        // if fitting worked: use mean value of the fits
        else{
          MinPositions[vpeds][asics][channels] = int(hMinPos[asics][channels]->GetMean());
        }
        // correction if Peak Post fits did not work
        // -> take value from previous amplitude
        for(int i=1; i<5; ++i){
          if(MinPositions[vpeds][asics][channels] < 10){
            MinPositions[vpeds][asics][channels] = MinPositions[vpeds-i][asics][channels];
          }
          if(MinPositions[vpeds][asics][channels] > 10) continue;
        }                
        // print results of fits
        std::cout << "Asic " << asics << " Channel " << channels << "   " << PeakPositions[vpeds][asics][channels] << "   " << MinPositions[vpeds][asics][channels] << std::endl;
      }
    }
    // saving, resetting, deleting the histograms
    for(int asics = 0; asics<ASICS; ++asics){
      for(int channels = 0; channels<CHANNELS; ++channels){
        hPeakPos[asics][channels]->Write();
        hPeakPos[asics][channels]->Reset();
        hMinPos[asics][channels]->Write();
        hMinPos[asics][channels]->Reset();        
        delete hPeakPos[asics][channels];
        delete hMinPos[asics][channels];        
      }
    }
  }

#ifdef Use_TFmaker
  // Create TfMaker
  ofstream entryfile;
  std::string entryfile_path = FilePrefix + "input.csv";
  std::remove(entryfile_path.c_str());
  entryfile.open(entryfile_path);
  entryfile << "event,pixel,row,column,blockphase,fci,fb,cell,vped,sample,adc\n";
  TfMaker tf(&vped[0],vped.size(), NMODULES, vped[0]);
#endif

  // create file to store number of cells with no TF entries
  std::string emptycell_name = OutDir + "emptycells_" + ModuleID + ".txt";
  fstream emptycell_file(emptycell_name, ios::out | ios::trunc);

  //  Begin Loop over measured Amplitudes
  for (uint16_t i = NegValues; i < vped.size(); i++) {

    // vectors to store ADC values
    std::vector< std::vector<float> > CellPeakADC(ASICS*CHANNELS*CELLS);
    std::vector< std::vector<float> > CellMinADC(ASICS*CHANNELS*CELLS);
    std::string InFile  = FilePrefix + Form("%d",vped[i]) + "_r1.tio";   //  Define Filename of read in EventFile

    // get information from event file
    EventFileReader reader(InFile.c_str());                     //  Open up the EventFile
    uint32_t packetsize = reader.GetPacketSize();               //  Get packet size of stored packets
    int NEvents         = reader.GetNEvents();                  //  Get number of stored events
    bool R1 = false;
    if (reader.HasCardImage("R1")) {
      R1 = reader.GetCardImage("R1")->GetValue()->AsBool();
      if (R1) {
        Offset = (float) reader.GetCardImage("OFFSET")->GetValue()->AsDouble();
        Scale = (float) reader.GetCardImage("SCALE")->GetValue()->AsDouble();
      }
    }

    cout << "File: " << i << "/" << vped.size()-NegValues << endl;
    cout << "Current amplitude = " << vped[i] << endl;
    cout << "Offset: " << Offset << " Scale: " << Scale << endl;
    std::cout << "Total number of events in this File: " << NEvents << "\n" << std::endl;  //  Write to console

    // hist to store histograms with ADC mean/rms calculation
    TH1D *hADCmean = new TH1D("hADCmean","hADCmean",4000,0,4000);
    TH1D *hADCmean_neg = new TH1D("hADCmean_neg","hADCmean_neg",2000,-1000,1000);    

    int BadFitCnt = 0; // counter to store number of  bad fits

    // Begin Loop over single Events, Asics and channels in the EventFile
    for(int ii=0; ii < NEvents; ii++){
      if( ii % 5000 == 0){
        std::cout << "Currently processing Event " << ii << " of " << NEvents << "\r" << std::flush;
      } 
      bool GoodFit = false; // variable to store fit goodness
      float FittedCell = 0.0; // variable to store fitted cell

      for (int asics = 0; asics < ASICS; ++asics){

        //  look at the first packet to get Starting Block
        data          = reader.GetEventPacket(ii,asics);
        prec.Assign(data, packetsize);
        if(!prec.IsValid()) continue;

        ColID         = prec.GetColumn();
        RowID         = prec.GetRow();
        PhaseID       = prec.GetBlockPhase();
        StartingBlock = RowID+ColID*8;
        FirstCellId   = prec.GetFirstCellId();
              
        for (int iii = 0; iii < CHANNELS; iii++){
          Waveform* w = prec.GetWaveform(iii);              //  From EventFile i grab the iiith waveform from Event ii
          NSamples = w->GetSamples();                       //  Get the number of Samples in Waveform (should be constant)

          // Fit one channel of one asic every event
          // out of convenience: do this for the first channel of the first asic (A0 Ch0)
          if(asics == 0 && iii == 0 && i >= 10+NegValues && i <= 53+NegValues){
            // do the fits only for reasonable amplitudes (see also peak pos determination above)

            char histname1[100];
            sprintf(histname1, "Vped%d_Asic%d_Channel%d_Event%d", vped[i], asics, iii, ii);
            TH1I* hist1 = new TH1I(histname1,histname1,NSamples,0.,NSamples);  //  Histogram for each Waveform
            GoodFit = true;

            float value_calib1 = 0, value_calib2 = 0, value_calib3 = 0;
            for(int sample = 0; sample < NSamples; sample++){
              float value_calib = ((float) w->GetADC16bit(sample) / Scale) - Offset;
              hist1->SetBinContent(sample+1, value_calib);  // Set new Bin content (BinNR starts from 1)
              // quality control
              if( (value_calib1 > 500 && value_calib2 < 1) || (value_calib3 > 500 && value_calib2 < 1) || value_calib > 4000)
              {
                GoodFit = false;
              }              
              value_calib3 = value_calib2;
              value_calib2 = value_calib1;
              value_calib1 = value_calib;
            }

            // fit function
            TF1* llfit = new TF1("llfit","landau+landau(3)",0,NBLOCKS*32);
            llfit->SetParameter(0,vped[i]*11.0);
            llfit->SetParameter(1,PeakPositions[i][asics][iii]);
            llfit->SetParameter(2,3);
            llfit->SetParameter(3,vped[i]*(-2.75));
            llfit->SetParameter(4,MinPositions[i][asics][iii]);
            llfit->SetParameter(5,6.5);
            hist1->Fit("llfit","WWQR");

            // quality control
            if ( llfit->GetParameter(1) < 40 || llfit->GetParameter(1) > 65
                || llfit->GetMaximumX() < 40 || llfit->GetMaximumX() > 65
                || llfit->GetParameter(2) > 10
                || llfit->GetMinimumX() < 50 || llfit->GetMinimumX() > 90
                || llfit->GetParameter(5) > 20 )
            {
              GoodFit = false;
            }

            FittedCell = llfit->GetMaximumX();

            delete llfit;
            delete hist1;
          }
          int TakeBin = PEAKPOS;
          // if fit worked:
          if( GoodFit ){
            // Use calculated peak positions to get adc values
            // (accounts for differences in transit times)
            if( not(asics==0 && iii==0) && (i >= 10 + NegValues && i <= 53 + NegValues) ){
              TakeBin = int(FittedCell + (PeakPositions[i][asics][iii] - PeakPositions[i][0][0]));
            }
            // use value from fit for A0 Ch0
            else if(asics == 0 && iii == 0 && i >= 10 + NegValues && i <= 53 + NegValues){
              TakeBin = int(FittedCell);
            }
            // take peak positions for small/large amplitudes since fits wont work there
            if(i < 10 + NegValues) TakeBin = int(PeakPositions[10+NegValues][asics][iii]); // since no fit was done
            else if(i > 53 + NegValues) TakeBin = int(PeakPositions[53+NegValues][asics][iii]); // since no fit was done
            if(TakeBin < 10 || TakeBin > 80) TakeBin = PEAKPOS; // correction if something strange happened
          }
          // if fit did not work, take values from peak position determination
          // as a fallback option
          else{
            FittedCell = 0;
            if(i < 10 + NegValues) TakeBin = int(PeakPositions[10+NegValues][asics][iii]); // since no fit was done
            else if(i > 53 + NegValues) TakeBin = int(PeakPositions[53+NegValues][asics][iii]); // since no fit was done
            else TakeBin = int(PeakPositions[i][asics][iii]);
            // last fallback option if previous determination of peak positions did not work
            if(TakeBin < 10 || TakeBin > 80) TakeBin = PEAKPOS;
            BadFitCnt++;
          }
          // check if cell is on rising / trailing edge to detect pulse jumps
          // only important for large amplitudes since fit does not work there
          if(i>53+NegValues){
            float value_calib = ((float) w->GetADC16bit(TakeBin) / float(Scale)) - float(Offset);
            float value_calib2 = ((float) w->GetADC16bit(TakeBin-1) / float(Scale)) - float(Offset);
            float value_calib3 = ((float) w->GetADC16bit(TakeBin+1) / float(Scale)) - float(Offset);
            if( (value_calib2 < 0.8*value_calib || value_calib3 > 1.2*value_calib ||
                value_calib2 > 1.2*value_calib || value_calib3 < 0.8*value_calib) )
            {
              continue;
            }
          }

#ifdef Use_TFmaker
          tf.SetAmplitudeIndex(vped[i]); // Set Vped Index to Amplitude value of file
#endif
          // calculate actual cell for storage
          int peakmean_cell_static = 0;
          peakmean_cell_static = FirstCellId + TakeBin;
          // corrections
          if(StartingBlock%2 == 0 && PhaseID+TakeBin < 64) peakmean_cell_static = FirstCellId + TakeBin + 64;
          if(StartingBlock%2 == 0 && PhaseID+TakeBin >= 64) peakmean_cell_static = FirstCellId + TakeBin;
          if(StartingBlock%2 != 0 && PhaseID+TakeBin < 64) peakmean_cell_static = FirstCellId + TakeBin - 64;
          if(StartingBlock%2 != 0 && PhaseID+TakeBin >= 64) peakmean_cell_static = FirstCellId + TakeBin;
          if (peakmean_cell_static >= CELLS){
            peakmean_cell_static = peakmean_cell_static - CELLS;
          }
          float value_calib = ((float) w->GetADC16bit(TakeBin) / float(Scale)) - float(Offset);
          // if determined adc value makes sense: fill vector and tfmaker
          // (overflow or too large adc values)
          if( !(value_calib < 0 || (vped[i] > 999 && value_calib < 200) || value_calib > 4000) ){
            //Fill array with adc values
            CellPeakADC[asics*CHANNELS*CELLS+iii*CELLS+peakmean_cell_static].push_back(value_calib);
#ifdef Use_TFmaker
           // add adc value
           tf.AddSample(value_calib, TakeBin, MODULE_ID, asics*CHANNELS + iii, FirstCellId);
            entryfile << ii << "," << asics*CHANNELS + iii << "," << RowID << "," << ColID << "," << PhaseID << "," << FirstCellId << "," << StartingBlock << "," << peakmean_cell_static << "," << vped[i] << "," << TakeBin << "," << value_calib << "\n";
#endif
          }

          // possibility to store some diagnostic data
          /*
          if( asics == 0 && iii == 6 && peakmean_cell_static == 2846 ){

            char adcmeanname[50];
            sprintf(adcmeanname, "Amplitude%d Asic%d Channel%d Cell%d", vped[i], asics, iii, peakmean_cell_static);
            hADCmean->SetTitle(adcmeanname);
            hADCmean->Fill(value_calib);
          
            TCanvas *c2 = new TCanvas();
            TH1D *h2 = new TH1D("h2","h2",NSamples,0,NSamples);
            h2->SetTitle(adcmeanname);
            for(int blob=0; blob<NSamples; ++blob){
              value_calib = ((float) w->GetADC16bit(blob) / Scale) - Offset;
              h2->SetBinContent(blob+1, value_calib);
            }
            h2->Draw();
            TLine *line = new TLine(TakeBin+0.5, h2->GetMinimum(), TakeBin+0.5, h2->GetMaximum()+h2->GetMaximum()*0.1);
            line->SetLineColor(kRed);
            line->Draw();
            TLine *line2 = new TLine(FittedCell, h2->GetMinimum(), FittedCell, h2->GetMaximum()+h2->GetMaximum()*0.1);
            line2->SetLineColor(kBlue);
            line2->Draw();
            char pngname[50];
            sprintf(pngname, "%d_Ampl%d_Asic%d_channel%d_cell%d.png", ii, vped[i], asics, iii, peakmean_cell_static);
            c2->SaveAs(pngname);
            h2->Write();
            delete h2;
            delete c2;
             
          }
          */

          // ### negative values ### //

          if(vped[i] == 48 || vped[i] == 112 || vped[i] == 200 || vped[i] == 280 
              || vped[i] == 600 || vped[i] == 1048 || vped[i] == 1496 || vped[i] == 1752 ){
            // only needed for certain vped values (see beginging of script)

            // TODO: decide on method for min pos cell determination
            // method 1:
            // use fit to account for pulse jitters
            // use peak positions to account for differences in transit times
            /*
            int TakeBinNeg = 0;
            if( GoodFit ){
              // Use calculated peak positions to get adc values
              if( not(asics==0 && iii==0) && (i >= 10 + NegValues && i <= 53 + NegValues) ){
                TakeBinNeg = int(FittedCell + (MinPositions[i][asics][iii] - PeakPositions[i][0][0]));
              }
              // use value from fit
              else if(asics == 0 && iii == 0 && i >= 10 + NegValues && i <= 53 + NegValues){
                TakeBinNeg = int(FittedCell + MinPositions[i][asics][iii] - PeakPositions[i][asics][iii]);
              }
              // take peak positions for small/large amplitudes since fits wont work there
              if(i < 10 + NegValues) TakeBinNeg = int(MinPositions[10+NegValues][asics][iii]); // since no fit was done
              else if(i > 53 + NegValues) TakeBinNeg = int(MinPositions[53+NegValues][asics][iii]); // since no fit was done
              if(TakeBinNeg < 50 || TakeBinNeg > 95) TakeBinNeg = 70; // correction if something strange happened
            }
            // if fit did not work, take values from peak position determination
            else{
              FittedCell = 0;
              if(i < 10 + NegValues) TakeBinNeg = int(MinPositions[10+NegValues][asics][iii]); // since no fit was done
              else if(i > 53 + NegValues) TakeBinNeg = int(MinPositions[53+NegValues][asics][iii]); // since no fit was done
              else TakeBinNeg = int(MinPositions[i][asics][iii]);
              if(TakeBinNeg < 10 || TakeBinNeg > 80) TakeBinNeg = 70; // correction if something strange happened
              BadFitCnt++;
            }
            */

            // method 2:
            // only take determinded mean minimum positions
            int TakeBinNeg = 0;
            if(i < (10 + NegValues)) TakeBinNeg = int(MinPositions[10+NegValues][asics][iii]); // since no fit was done
            else if(i > (53 + NegValues)) TakeBinNeg = int(MinPositions[53+NegValues][asics][iii]); // since no fit was done
            else TakeBinNeg = int(MinPositions[i][asics][iii]); 
            if(TakeBinNeg < 50 || TakeBinNeg > 95) TakeBinNeg = 70; // correction if something strange happened

            // calculate actual cell for storage
            peakmean_cell_static = FirstCellId + TakeBinNeg;
            // corrections
            int f = 64 * (1 - 2 * (StartingBlock % 2));
            int factor = (((PhaseID + TakeBinNeg) / 32) % 2) * f;
            peakmean_cell_static = FirstCellId + TakeBinNeg + factor;


            if(StartingBlock%2 == 0 && PhaseID+TakeBinNeg < 64) peakmean_cell_static = FirstCellId + TakeBinNeg + 64;
            if(StartingBlock%2 == 0 && PhaseID+TakeBinNeg >= 64) peakmean_cell_static = FirstCellId + TakeBinNeg;
            if(StartingBlock%2 != 0 && PhaseID+TakeBinNeg < 64) peakmean_cell_static = FirstCellId + TakeBinNeg - 64;
            if(StartingBlock%2 != 0 && PhaseID+TakeBinNeg >= 64) peakmean_cell_static = FirstCellId + TakeBinNeg;
            if (peakmean_cell_static >= CELLS){
              peakmean_cell_static = peakmean_cell_static - CELLS;
            }
            float value_calib_neg = ((float) w->GetADC16bit(TakeBinNeg) / Scale) - Offset;

            // save adc values if they make sense
            if( !(value_calib_neg < -600) ){
              CellMinADC[asics*CHANNELS*CELLS+iii*CELLS+peakmean_cell_static].push_back(value_calib_neg);
#ifdef Use_TFmaker
              // set vped to negative values
              int16_t vped_neg;
              if(vped[i] == 1752) vped_neg = vped[0];
              else if(vped[i] == 1496) vped_neg = vped[1];
              else if(vped[i] == 1048) vped_neg = vped[2];
              else if(vped[i] == 600) vped_neg = vped[3];
              else if(vped[i] == 280) vped_neg = vped[4];
              else if(vped[i] == 200) vped_neg = vped[5];
              else if(vped[i] == 112) vped_neg = vped[6];
              else if(vped[i] == 48) vped_neg = vped[7];
              tf.SetAmplitudeIndex(vped_neg);
#endif
#ifdef Use_TFmaker
              // add adc value
              tf.AddSample(value_calib_neg, TakeBinNeg, 0, asics*CHANNELS + iii, FirstCellId);
              entryfile << ii << "," << asics*CHANNELS + iii << "," << RowID << "," << ColID << "," << PhaseID << "," << FirstCellId << "," << StartingBlock << "," << peakmean_cell_static << "," << vped_neg << "," << TakeBinNeg << "," << value_calib_neg << "\n";
#endif
            }

            // posibility to store diagnostic data
            /*
            if( asics == 0 && iii == 7 && peakmean_cell_static == 69){
              char adcmeanname[50];
              sprintf(adcmeanname, "Amplitude%d Asic%d Channel%d Cell%d negative", vped[i], asics, iii, peakmean_cell_static);
              hADCmean_neg->SetTitle(adcmeanname);
              hADCmean_neg->Fill(value_calib_neg);
            }
            */

          }
          delete w;
          
        }  //  Channel loop end
      }   //  Event loop end
    }

  } //  Amplitude loop close
  emptycell_file.close();

#ifdef Use_TFmaker
  tf.Save(OutFile.c_str(), 8, false); //  Save TfMaker file
  entryfile.close();
#endif
  tfile->Close(); // close TFile
 
  return 1;
}


// functions
int GetArrayPos(uint16_t asic, uint16_t channel, uint16_t arr[][CHANNELS], uint16_t size){
  int nr = 0;
  for(int i=0; i<size; ++i){
    if(arr[asic][i] == channel) nr = i;
  }
  return nr;
}
