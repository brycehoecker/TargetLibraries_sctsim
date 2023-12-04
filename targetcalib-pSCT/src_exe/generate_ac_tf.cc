/*
Script to create AC Transer functions with TargetIO files as input
which stores results in TargetCalib files (and creates extra plots).

This script is a new, better structured and faster version of the 
script used before.

For general usage see "ShowUsage()" function below.

Needed for usage:
  - Pedestal calibrated input files with pulses with varying input amplitudes
    (one amplitude per file)
  - For negative Vpeds:
    - Use undershoot after pulse (current method)
    - Use negative pulses (takes longer)
  - Folder for output needs to be already existing
  - TargetCalib creation is actived by preprocessor directive
  - Software: ROOT, TargetDriver, TargetIO, TargetCalib

Caution:
  - Use of negative pulses works but not (yet) tested within this script
  - Option parse not (yet) failproof

author: david.jankowsky@fau.de
*/

#include <vector>
#include <ostream>
#include <cmath>
#include <numeric>
#include <algorithm>

// Target
#include "TargetDriver/DataPacket.h"
#include "TargetDriver/Waveform.h"
#include "TargetIO/EventFileReader.h"
#include "TargetCalib/TfMaker.h"

// Root
#include <TH2F.h>
#include <TH1I.h>
#include <TF1.h>
#include <TGraph.h>
#include <TFile.h>
#include <TCanvas.h>

// Create a TargetCalib File
#define Use_TFmaker

// Definitions of some constants
// Module
const int ASICS           = 4; // number of asics
const int CHANNELS        = 16; // number of channels
const int CELLS           = 4096; // number of cells in storage
const int NBLOCKS         = 3; // number of blocks in readout window
// Transfer Function
const int MODULE_ID       = 0; // Module ID, only needed for TargetCalib::TfMaker
const int NMODULES        = 1; // only needed for TargetCalib::TfMaker
const int MAX_VPED        = 3000; // max value of input amplitudes
const int FITRANGE_LOW    = 42; // starting point for peak pos (in mV)
const int FITRANGE_HIGH   = 1800; // starting point for peak pos (in mV)
const int NFITS           = 210; // nr of fits for peak position determination; >200 is normally enough
const int FIT_ASIC        = 0; // Asic for pulse fit
const int FIT_CHANNEL     = 0; // channel for pulse fit
const float PEAKPOS       = 45.00; // guessed peak position as fallback option

void ShowUsage();



class TFgenerator{
// A class which manages the creation of AC TransferFunctions

private:
  // CTA::Target*
  CTA::TargetCalib::TfMaker *fTfMaker = nullptr; 
  CTA::TargetDriver::DataPacket *fPacket = nullptr;
  CTA::TargetDriver::Waveform fWf;

  // Target IO Info
  float fOffset;
  float fScale;
  uint16_t fPacketsize;
  uint16_t fNrSamples;
  uint8_t* fData;

  std::string fModuleID;
  std::string fInPath;
  std::string fOutPath;
  std::string fFilePrefix;

  // ROOT
  TH1I *fHist; // histogram for fitting
  TF1 *fFit; // fit function

  // Input files and booleans
  std::vector<float> fVpedsInput; // Vpeds of input files
  std::vector<float> fVpeds; // Used values for Vped
  uint16_t fNrFiles; // nr of files
  uint16_t fNrNegValues; // nr of negative values
  bool fNegMethod; // use special method for negative values
  bool fDoBaselineCorr;
  bool fDoPlots;

  // vectors for data storage
  std::vector<float> PeakADC_mean[ASICS][CHANNELS][CELLS];
  std::vector<float> PeakADC_stdev[ASICS][CHANNELS][CELLS];
  std::map<float, float> PeakPosMap[ASICS][CHANNELS];
  std::map<float, float> MinPosMap[ASICS][CHANNELS];
  std::vector< float> MeanPedestalValues[ASICS][CHANNELS];
  float MeanPedestal[ASICS][CHANNELS];


public:
  TFgenerator( std::string InPath, std::string OutPath, std::string ModuleID, bool NegMethod, bool DoBaselineCorr, bool DoPlots ){
    // constructor which initializes basic variables

    fModuleID = ModuleID;
    fInPath = InPath;
    fOutPath = OutPath + ModuleID + "/";
    fFilePrefix = InPath + "ac_tf_data_" + ModuleID + "/Amplitude_";

    std::cout << "Module " << fModuleID << std::endl;
    std::cout << "InPath: " << fInPath << std::endl;
    std::cout << "OutPath: " << fOutPath << std::endl;

    fNrFiles = 0;
    ReadFiles(InPath, ModuleID);
    GetTargetIOInfo();

    fDoBaselineCorr = DoBaselineCorr;
    fDoPlots = DoPlots;

    // special negative methods
    // true voltages of undershoot need to be measured
    if( NegMethod ){ std::cout << "Using special method for negative input amplitudes" << std::endl;
      fNegMethod = NegMethod;
      fNrNegValues = 0;
      for (auto const &vped : fVpedsInput){
        if(vped == 1752){ fVpeds.push_back(-363); fNrNegValues++; }
        else if(vped == 1496){ fVpeds.push_back(-310); fNrNegValues++; }
        else if(vped == 1048){ fVpeds.push_back(-217); fNrNegValues++; }
        else if(vped == 600){ fVpeds.push_back(-124); fNrNegValues++; }
        else if(vped == 280){ fVpeds.push_back(-58); fNrNegValues++; }
        else if(vped == 200){ fVpeds.push_back(-41); fNrNegValues++; }
        else if(vped == 112){ fVpeds.push_back(-23); fNrNegValues++; }
        else if(vped == 48){ fVpeds.push_back(-10); fNrNegValues++; }  
      }
      std::sort(fVpeds.begin(), fVpeds.end());
    }

    // Prepare arrays, vectors
    for (int iasic = 0; iasic < ASICS; ++iasic){
      for (int ichan = 0; ichan< CHANNELS; ++ichan){
        MeanPedestal[iasic][ichan] = 0.0;
        for(int icell = 0; icell < CELLS; ++icell){
          PeakADC_mean[iasic][ichan][icell].reserve(fVpeds.size());
          PeakADC_stdev[iasic][ichan][icell].reserve(fVpeds.size());
        }
      }
    }

    // ROOT
    fHist = new TH1I("","",fNrSamples,0.0,fNrSamples);
    fFit = new TF1("fFit","landau+landau(3)",0,NBLOCKS*32);

#ifdef Use_TFmaker
    fTfMaker = new CTA::TargetCalib::TfMaker(fVpeds, NMODULES, CELLS);
#endif
  }


  ~TFgenerator(){
    // destructor

#ifdef Use_TFmaker
    delete fTfMaker;
#endif
    delete fPacket;

    delete fHist;
    delete fFit;
  }
  

  void ReadFiles(std::string InPath, std::string ModuleID){
    // function tp read in file list to process

    std::cout << "Reading files" <<std::endl;

    for(int i = 0; i < MAX_VPED+1; i++){
      std::string InFile  = fFilePrefix + Form("%d",i) + "_r1.tio";
      if (!std::ifstream(InFile)) {
        continue;
      }
       else{
        std::cout << "Pulse amplitude " << i << " mV" << std::endl;
        fVpedsInput.push_back(i);
        fNrFiles++;     
      }
    }
    fVpeds = fVpedsInput;
    std::cout << "Found " << fNrFiles << " files" << std::endl;
  }


  void GetTargetIOInfo(){
    // get TargetIO information from first file

    std::cout << "Reading TargetIO information" << std::endl;

    std::string InFile  = fFilePrefix + Form("%d",(int)fVpedsInput[0]) + "_r1.tio";
    CTA::TargetIO::EventFileReader fReader(InFile.c_str());

    fPacketsize = fReader.GetPacketSize();
    fData = fReader.GetEventPacket(0,0);
    fPacket = new CTA::TargetDriver::DataPacket(fPacketsize);
    fPacket->Assign(fData, fPacketsize);
    fPacket->AssociateWaveform(0, fWf);
    fNrSamples = fWf.GetSamples();

    bool R1 = false;
    if (fReader.HasCardImage("R1")) {
      R1 = fReader.GetCardImage("R1")->GetValue()->AsBool();
      if (R1) {
        fOffset = (float) fReader.GetCardImage("OFFSET")->GetValue()->AsDouble();
        fScale = (float) fReader.GetCardImage("SCALE")->GetValue()->AsDouble();
      }
    }
  }

  void GetMeanPulsePosition(){
    // determine mean peak position in readout window
    // for each asic and channel
    // needed to correct signal time variations
    // has to be done before calculating TFs

    std::cout << "Searching for peak positins in readout window" << std::endl;

    std::vector<float>::iterator it_vped, low, up;
    // since not all amplitudes can be easily fitted
    // get a useful range to do this
    low = std::lower_bound (fVpedsInput.begin(), fVpedsInput.end(), FITRANGE_LOW);
    up = std::upper_bound (fVpedsInput.begin(), fVpedsInput.end(), FITRANGE_HIGH);

    for(it_vped = low; it_vped != up; ++it_vped){

      std::string InFile = fFilePrefix + Form("%d",(int)*it_vped) + "_r1.tio";
      std::cout << InFile << std::endl;
      CTA::TargetIO::EventFileReader fReader(InFile.c_str());
      int NEvents = fReader.GetNEvents();
      std::cout << "Pulse amplitude " << *it_vped << std::endl;
      std::cout << "Using " << NFITS << " events of " << NEvents << " for calculations" << std::endl;

      for(int iasic = 0; iasic<ASICS; ++iasic){
        for(int ichan = 0; ichan<CHANNELS; ++ichan){

          std::vector< float > PeakPos;
          std::vector< float > MinPos;

          for(int ievt = 0; ievt<NEvents; ++ievt){
            
            fData = fReader.GetEventPacket(ievt,iasic);
            fPacket->Assign(fData, fPacketsize);
            if(!fPacket->IsValid()) continue;

            fPacket->AssociateWaveform(ichan, fWf);
            float xmax, xmin;
            bool PeakGoodFit = FitWf(*it_vped, ievt, iasic, ichan, xmax, xmin);
            if( !PeakGoodFit ) continue;

            PeakPos.push_back(xmax);
            MinPos.push_back(xmin);

            if(PeakPos.size() > NFITS && MinPos.size() > fNrFiles) break;
          }
          float mean = std::accumulate(PeakPos.begin(), PeakPos.end(), 0.0) / PeakPos.size();
          float mean_min = std::accumulate(MinPos.begin(), MinPos.end(), 0.0) / MinPos.size();

          // Save results to maps
          if( it_vped == low){
            for(std::vector<float>::iterator it = fVpedsInput.begin(); it != low+1; ++it){
              PeakPosMap[iasic][ichan].insert(std::pair<float, float>(*it, mean ));
              MinPosMap[iasic][ichan].insert(std::pair<float, float>(*it, mean_min ));
            }
          }
          else if(it_vped == up-1){
            for(std::vector<float>::iterator it = up-1; it != fVpedsInput.end(); ++it){
              PeakPosMap[iasic][ichan].insert(std::pair<float, float>(*it, mean ));
              MinPosMap[iasic][ichan].insert(std::pair<float, float>(*it, mean_min ));
            }
          }
          else{
            PeakPosMap[iasic][ichan].insert(std::pair<float, float>(*it_vped, mean ));
            MinPosMap[iasic][ichan].insert(std::pair<float, float>(*it_vped, mean_min ));
          }
          std::cout << iasic << "\t" << ichan << "\t" << mean << "\t" << mean_min << std::endl;
        }
      }
    }
  }

  void CalculateTF(){
    // function to calculate values for TF
    // manages also TargetCalib TFs

    std::cout << "Getting ADC values for TFs" << std::endl;
    for (auto const &vped : fVpedsInput) {

      std::string InFile  = fFilePrefix + Form("%d",int(vped)) + "_r1.tio";
      CTA::TargetIO::EventFileReader fReader(InFile.c_str());
      int NEvents = fReader.GetNEvents();
      std::cout << "Current amplitude = " << vped << " with " << NEvents << " events" << std::endl;
      // vectors to store ADC values
      std::vector< std::vector<float> > CellPeakADC(ASICS*CHANNELS*CELLS);
      std::vector< std::vector<float> > CellMinADC(ASICS*CHANNELS*CELLS);

      // Begin Loop over single Events, Asics and channels in the EventFile
      for(int ievt=0; ievt < NEvents; ievt++){
        if( ievt % 5000 == 0) std::cout << "Processing Event " << ievt << " of " << NEvents << "\r" << std::flush;
        
        bool GoodFit = false; // variable to store fit goodness
        float FittedCell = 0.0; // variable to store fitted cell
        float xmin;
        // Fit a Wf to get an eventwise peak position
        GoodFit = FitAsCh(fReader, vped, ievt, FIT_ASIC, FIT_CHANNEL, FittedCell, xmin);

        for (int iasic = 0; iasic < ASICS; ++iasic){
          fData = fReader.GetEventPacket(ievt, iasic);
          fPacket->Assign(fData, fPacketsize);
          if(!fPacket->IsValid()) continue;

          int FirstCellId = fPacket->GetFirstCellId();
                
          for (int ichan = 0; ichan < CHANNELS; ++ichan){
            fPacket->AssociateWaveform(ichan, fWf);
            float baseline_corr = 0.0;
            if(fDoBaselineCorr) baseline_corr = GetBaselineCorrection(vped, iasic, ichan);
            GetADCvalues(GoodFit, FittedCell, FirstCellId, baseline_corr, vped, iasic, ichan, CellPeakADC);
            if(fNegMethod) GetNegADCvalues(FirstCellId, baseline_corr, vped, iasic, ichan, CellMinADC);
          }
        }
      }
      if(fDoPlots) CalculateMeanADC(CellPeakADC, CellMinADC, vped);
    }
  }


  bool GetADCvalues(bool GoodFit, float FittedCell, int FirstCellId, 
    float baseline_corr, float vped, int iasic, int ichan, std::vector< std::vector<float> >& CellPeakADC){
    // function to get ADC value for a certain bin
    // value is stored in class member variable
    
    int TakeBin = PEAKPOS;      
    GetPeakPos(GoodFit, FittedCell, vped, iasic, ichan, TakeBin);

#ifdef Use_TFmaker
    fTfMaker->SetAmplitudeIndex(vped); // Set Vped Index to Amplitude value of file
#endif
    // calculate actual cell for storage
    int peak_cell = CTA::TargetCalib::GetCellIDTC(FirstCellId, TakeBin);
    float value_calib = ((float) fWf.GetADC16bit(TakeBin) / float(fScale)) - float(fOffset);

    // check if cell is on rising / trailing edge to detect pulse jumps
    // only important for large amplitudes since fit does not work there
    if(vped > FITRANGE_HIGH){
      float value_calib2 = ((float) fWf.GetADC16bit(TakeBin-1) / float(fScale)) - float(fOffset);
      float value_calib3 = ((float) fWf.GetADC16bit(TakeBin+1) / float(fScale)) - float(fOffset);
      if( (value_calib2 < 0.8*value_calib || value_calib3 > 1.2*value_calib || 
        value_calib2 > 1.2*value_calib || value_calib3 < 0.8*value_calib) )
          return false;
    }
    value_calib = value_calib - baseline_corr;

    // if determined adc value makes sense: fill vector and tfmaker
    // (overflow or too large adc values)
    if( !(value_calib < 0 || (vped > 999 && value_calib < 200) || value_calib > 4000) ){
      //Fill array with adc values
      if(fDoPlots) CellPeakADC[iasic*CHANNELS*CELLS+ichan*CELLS+peak_cell].push_back(value_calib);
#ifdef Use_TFmaker
      // add adc value
      fTfMaker->AddSample(value_calib, TakeBin, MODULE_ID, iasic*CHANNELS + ichan, FirstCellId);  
#endif
      return true;
    }
    return false;
  }


  void GetPeakPos(bool GoodFit, float FittedCell, float vped, int asic, int chan, int &TakeBin){
    // Function to calculate peak position for certain channel

    if( GoodFit ){
      if( asic == FIT_ASIC && chan == FIT_CHANNEL){
        TakeBin = int(FittedCell);
      }
      else{
        TakeBin = int(FittedCell + (PeakPosMap[asic][chan][vped] - PeakPosMap[FIT_ASIC][FIT_CHANNEL][vped]));
      }
    }
    else{
      TakeBin = PeakPosMap[asic][chan][vped];
    }
    // fallback option if previous determination of peak positions did not work
    if(TakeBin < 10 || TakeBin > 80) TakeBin = PEAKPOS;
  }


  float GetBaselineCorrection(float vped, int asic, int chan){
    // function to correct baseline shifts (due to temperatures)

    float pedmean = 0, pedsum = 0;
    if(vped < 550){ // calculate mean baseline for every event below 550 mV pulses
      for(int pedbin = 0; pedbin < 25; ++pedbin){ // take first 25 bins
        pedsum += ((float) fWf.GetADC16bit(pedbin) / float(fScale)) - float(fOffset);
      }
      pedmean = pedsum / double(25);
      if(vped > 400) MeanPedestalValues[asic][chan].push_back(pedmean); // calculate mean baseline for a few amplitudes to use later
      return pedmean;
    }
    else if(std::fabs(MeanPedestal[asic][chan]) < 1e-6 && MeanPedestalValues[asic][chan].size() > 0){
      MeanPedestal[asic][chan] = std::accumulate(MeanPedestalValues[asic][chan].begin(), MeanPedestalValues[asic][chan].end(), 0.0)
        / MeanPedestalValues[asic][chan].size();
        return MeanPedestal[asic][chan];
    }
    else if(MeanPedestalValues[asic][chan].size() == 0) return 0;
    else return MeanPedestal[asic][chan];
  }


  void GetNegADCvalues(int FirstCellId, float baseline_corr, 
    float vped, int iasic, int ichan, std::vector< std::vector<float> >& CellMinADC){
    // Get ADC values for negative input amplitudes
    // choosable between different methods

    if(vped == 48 || vped == 112 || vped == 200 || vped == 280 
      || vped == 600 || vped == 1048 || vped == 1496 || vped == 1752 ){
              
      int TakeBinNeg = 0;
      GetNegPeakPos(vped, iasic, ichan, TakeBinNeg);
                
      // calculate actual cell for storage
      int peak_cell = CTA::TargetCalib::GetCellIDTC(FirstCellId, TakeBinNeg);
      float value_calib_neg = ((float) fWf.GetADC16bit(TakeBinNeg) / fScale) - fOffset;
      value_calib_neg = value_calib_neg - baseline_corr;

      // save adc values if they make sense
      if( !(value_calib_neg < -600) ){
        if(fDoPlots) CellMinADC[iasic*CHANNELS*CELLS+ichan*CELLS+peak_cell].push_back(value_calib_neg);
#ifdef Use_TFmaker
        if(vped == 1752) fTfMaker->SetAmplitudeIndex(-363);
        else if(vped == 1496) fTfMaker->SetAmplitudeIndex(-310);
        else if(vped == 1048) fTfMaker->SetAmplitudeIndex(-217);
        else if(vped == 600) fTfMaker->SetAmplitudeIndex(-124);
        else if(vped == 280) fTfMaker->SetAmplitudeIndex(-58);
        else if(vped == 200) fTfMaker->SetAmplitudeIndex(-41);
        else if(vped == 112) fTfMaker->SetAmplitudeIndex(-23);
        else if(vped == 48) fTfMaker->SetAmplitudeIndex(-10);
#endif
#ifdef Use_TFmaker
      // add adc value
        fTfMaker->AddSample(value_calib_neg, TakeBinNeg, 0, iasic*CHANNELS + ichan, FirstCellId); 
#endif
      }
    } 
  }


  bool GetNegPeakPos(float vped, int iasic, int ichan, int &TakeBinNeg){
    // get position of negative pulse

    TakeBinNeg = MinPosMap[iasic][ichan][vped];
    if(TakeBinNeg < 50 || TakeBinNeg > 95) TakeBinNeg = 70; // correction if something strange happened

    return true;
  }


  void CalculateMeanADC(std::vector< std::vector<float> >& CellPeakADC, std::vector< std::vector<float> >& CellMinADC, float vped){
    // calculate mean adc values for an amplitude/asic/channel, store it in member variable
    // not needed for TargetCalib

    for(int iasic = 0; iasic<ASICS; ++iasic){
      for (int ichan = 0; ichan < CHANNELS; ++ichan){
        for (int icell=0; icell < CELLS; ++icell){
          float mean, stdev;
          float mean_neg, stdev_neg;
          if(CellPeakADC[iasic*CHANNELS*CELLS+ichan*CELLS+icell].size() < 0.1){
            // if no measurement for certain sell: set to zero
            mean = 0;
            stdev = 0;
          }
          else{
            float sum = std::accumulate(CellPeakADC[iasic*CHANNELS*CELLS+ichan*CELLS+icell].begin(), 
              CellPeakADC[iasic*CHANNELS*CELLS+ichan*CELLS+icell].end(), 0.0);
            mean = sum/CellPeakADC[iasic*CHANNELS*CELLS+ichan*CELLS+icell].size();            
            float sq_sum = std::inner_product(CellPeakADC[iasic*CHANNELS*CELLS+ichan*CELLS+icell].begin(), 
              CellPeakADC[iasic*CHANNELS*CELLS+ichan*CELLS+icell].end(), CellPeakADC[iasic*CHANNELS*CELLS+ichan*CELLS+icell].begin(), 0.0);
            stdev = std::sqrt(sq_sum / CellPeakADC[iasic*CHANNELS*CELLS+ichan*CELLS+icell].size() - mean * mean);
            if( std::isnan(stdev) ) stdev = 0; // check for miscalculations
          }
          std::ptrdiff_t pos;
          pos = std::find(fVpeds.begin(), fVpeds.end(), vped) - fVpeds.begin();
          PeakADC_mean[iasic][ichan][icell][pos] = mean;
          PeakADC_stdev[iasic][ichan][icell][pos] = stdev;

          //negative values
          if(fNegMethod){
            if(CellMinADC[iasic*CHANNELS*CELLS+ichan*CELLS+icell].size() < 0.1){
              // if no mesurement for certain sell: set to zero
              mean_neg = 0;
              stdev_neg = 0;
            }
            else{
              float sum_neg = std::accumulate(CellMinADC[iasic*CHANNELS*CELLS+ichan*CELLS+icell].begin(), 
                CellMinADC[iasic*CHANNELS*CELLS+ichan*CELLS+icell].end(), 0.0);
              mean_neg = sum_neg/CellMinADC[iasic*CHANNELS*CELLS+ichan*CELLS+icell].size();
              float sq_sum_neg = std::inner_product(CellMinADC[iasic*CHANNELS*CELLS+ichan*CELLS+icell].begin(), 
                CellMinADC[iasic*CHANNELS*CELLS+ichan*CELLS+icell].end(), CellMinADC[iasic*CHANNELS*CELLS+ichan*CELLS+icell].begin(), 0.0);
              stdev_neg = std::sqrt(sq_sum_neg / CellMinADC[iasic*CHANNELS*CELLS+ichan*CELLS+icell].size() - mean_neg * mean_neg);
              if( std::isnan(stdev_neg) ) stdev_neg = 0;
            }
          
            // store values for negative amplitudes
            if(vped == 1752){
              pos = std::find(fVpeds.begin(), fVpeds.end(), -363) - fVpeds.begin();
              PeakADC_mean[iasic][ichan][icell][pos] = mean_neg;
              PeakADC_stdev[iasic][ichan][icell][pos] = stdev_neg;}
            else if(vped == 1496){
              pos = std::find(fVpeds.begin(), fVpeds.end(), -310) - fVpeds.begin();
              PeakADC_mean[iasic][ichan][icell][pos] = mean_neg;
              PeakADC_stdev[iasic][ichan][icell][pos] = stdev_neg;}
            else if(vped == 1048){
              pos = std::find(fVpeds.begin(), fVpeds.end(), -217) - fVpeds.begin();
              PeakADC_mean[iasic][ichan][icell][pos] = mean_neg;
              PeakADC_stdev[iasic][ichan][icell][pos] = stdev_neg;}
            else if(vped == 600){
              pos = std::find(fVpeds.begin(), fVpeds.end(), -124) - fVpeds.begin();
              PeakADC_mean[iasic][ichan][icell][pos] = mean_neg;
              PeakADC_stdev[iasic][ichan][icell][pos] = stdev_neg;}
            else if(vped == 280){
              pos = std::find(fVpeds.begin(), fVpeds.end(), -58) - fVpeds.begin();
              PeakADC_mean[iasic][ichan][icell][pos] = mean_neg;
              PeakADC_stdev[iasic][ichan][icell][pos] = stdev_neg;}
            else if(vped == 200){
              pos = std::find(fVpeds.begin(), fVpeds.end(), -41) - fVpeds.begin();
              PeakADC_mean[iasic][ichan][icell][pos] = mean_neg;
              PeakADC_stdev[iasic][ichan][icell][pos] = stdev_neg;}
            else if(vped == 112){
              pos = std::find(fVpeds.begin(), fVpeds.end(), -23) - fVpeds.begin();
              PeakADC_mean[iasic][ichan][icell][pos] = mean_neg;
              PeakADC_stdev[iasic][ichan][icell][pos] = stdev_neg;}
            else if(vped == 48){
              pos = std::find(fVpeds.begin(), fVpeds.end(), -10) - fVpeds.begin();
              PeakADC_mean[iasic][ichan][icell][pos] = mean_neg;
              PeakADC_stdev[iasic][ichan][icell][pos] = stdev_neg;}
          }
        }
      }
    }
  }


  bool FitAsCh(CTA::TargetIO::EventFileReader &fReader, float vped, int evt, int asic, int chan, 
    float &xmax, float &xmin){
    // fit a function to the waveform of a certain asic/channel

    if( vped < FITRANGE_LOW || vped > FITRANGE_HIGH) return false;
    else{
      fData = fReader.GetEventPacket(evt, asic);
      fPacket->Assign(fData, fPacketsize);
      fPacket->AssociateWaveform(chan, fWf);
      return FitWf(vped, evt, asic, chan, xmax, xmin);
    }
  }


  bool FitWf(float vped, int evt, int asic, int chan,
    float &xmax, float &xmin){
    // Fit a waveform with help of a root histogram

    for(int sample = 0; sample < fNrSamples; ++sample){
      float value_calib = ((float) fWf.GetADC16bit(sample) / fScale) - fOffset;
      fHist->SetBinContent(sample+1, value_calib);
    }
    if( DoFit(vped, xmax, xmin) ){
      fHist->Reset();
      return 1;
    }
    else return 0;
  }


  bool DoFit(float vped, float &xmax, float &xmin){
    // Do a double landau fit

    if(fFit->GetParameter(0) < 1e-6 && vped > 0.0){
      fFit->SetParameter(0,vped*11.0);
      fFit->SetParameter(1,PEAKPOS);
      fFit->SetParameter(2,3.0);
      fFit->SetParameter(3,vped*(-2.75));
      fFit->SetParameter(4,PEAKPOS+21);
      fFit->SetParameter(5,6.5);
    }    
    else if(fFit->GetParameter(0) > -1e-6 && vped < 0.0){
      fFit->SetParameter(0,vped*4.0);
      fFit->SetParameter(1,PEAKPOS);
      fFit->SetParameter(2,3.0);
      fFit->SetParameter(3,vped*(-1.5));
      fFit->SetParameter(4,PEAKPOS+34);
      fFit->SetParameter(5,6.5);
    }
    
    fHist->Fit("fFit","WWQR");

    xmax = fFit->GetMaximumX();
    xmin = fFit->GetMinimumX();

    //  Quality Controll stage 2: When Fit is not good move on!
    if ( fFit->GetParameter(1) < 40 || fFit->GetParameter(1) > 65 
        || xmax < 40 || xmax > 65
        || fFit->GetParameter(2) > 10
        || xmin < 50 || xmin > 90 
        || fFit->GetParameter(5) > 20 )
    {
      return 0;
    }

    return 1;
  }


  void SaveTFs(){
    // Saves the TargetCalib files

#ifdef Use_TFmaker
  fTfMaker->SaveTfInput(fOutPath + "TF_File_" + fModuleID + ".tcal");
  fTfMaker->Save(fOutPath + "TFInput_File_" + fModuleID + ".tcal", 25, 0, true); //  Save TfMaker file
#endif
  }


  void DoPlots(){
    // Create TF plots as histograms and save in a rootfile
    // Has to be adjusted

    std::string tfile_name = fOutPath + "ac_tf_hist_plots_" + fModuleID + ".root";
    std::string OutDir = fOutPath;
    TFile *tfile = new TFile(tfile_name.c_str(), "RECREATE");

    std::cout << "Creating histogram TFs" << std::endl;
    const double bins[68+1] = {-363, -310, -217, -124, -58, -41, -23, -10,
      0, 6, 8, 12, 16, 20, 24, 28, 32, 36, 40, 48, 56, 64, 
      72, 80, 88, 96, 104, 112, 120, 136, 152, 168, 184, 200, 216, 232, 248,
      264, 280, 312, 344, 376, 408, 440, 472, 504, 536, 568, 600, 664, 728, 792,
      856, 920, 984, 1048, 1112, 1176, 1240, 1368, 1496, 1624, 1752, 1880,
      2008, 2136, 2264, 2392, 2500};
    TH2F *hTFs_all = new TH2F("TFs_all", "TFs_all",68,bins,4500,-500,4000);
    TH2F *hTFs[ASICS][CHANNELS];
    //TH2F *hTFs2[CHANNELS][64];
    //TH2F *hTFs3[CHANNELS][128];
    TH2F *hRMS[ASICS][CHANNELS];
    TH2F *hRMS_all = new TH2F("TFs_RMS_all", "TFs_RMS_all",68,bins,1000,0,50);
    //TH2F *hRMS2[CHANNELS][64];
    //TH2F *hRMS3[CHANNELS][128];
    for(int asics=0; asics<ASICS; ++asics){
      for(int channels=0; channels<CHANNELS; ++channels){

        char histoname[100];
        sprintf(histoname, "Asics%d_Channel%d",asics, channels);
        hTFs[asics][channels] = new TH2F(histoname,histoname,68,bins,4500,-500,4000);
        hTFs[asics][channels]->SetTitle(histoname);

        sprintf(histoname, "Asics%d_Channel%d_RMS",asics, channels);
        hRMS[asics][channels] = new TH2F(histoname,histoname,68,bins,1000,0,50);
        hRMS[asics][channels]->SetTitle(histoname);
       
        /*       
        if(asics==0){
          for(int i=0; i<128; ++i){
            sprintf(histoname, "Asics%d_Channel%d_sampling_%d",asics,channels,i);
            if(i<64) hTFs2[channels][i] = new TH2F(histoname,histoname,68,bins,4500,-500,4000);
            sprintf(histoname, "Asics%d_Channel%d_block_%d",asics,channels,i);
            hTFs3[channels][i] = new TH2F(histoname,histoname,68,bins,4500,-500,4000);

            sprintf(histoname, "Asics%d_Channel%d_RMS_sampling_%d",asics,channels,i);
            if(i<64) hRMS2[channels][i] = new TH2F(histoname,histoname,68,bins,1000,0,50);
            sprintf(histoname, "Asics%d_Channel%d_RMS_block_%d",asics,channels,i);
            hRMS3[channels][i] = new TH2F(histoname,histoname,68,bins,1000,0,50);
          }
        }
        */

        for(int cells=0; cells<CELLS; ++cells){
          for(uint16_t ivped=0; ivped<fVpeds.size(); ++ivped){

            hTFs_all->Fill(fVpeds[ivped], PeakADC_mean[asics][channels][cells][ivped]);
            hRMS_all->Fill(fVpeds[ivped], PeakADC_stdev[asics][channels][cells][ivped]);


            hTFs[asics][channels]->Fill(fVpeds[ivped], PeakADC_mean[asics][channels][cells][ivped]);
            //if(asics==0) hTFs2[channels][cells%64]->Fill(fVpeds[ivped], PeakADC_mean[asics][channels][cells][ivped]);
            //if(asics==0) hTFs3[channels][cells/32]->Fill(fVpeds[ivped], PeakADC_mean[asics][channels][cells][ivped]);

            hRMS[asics][channels]->Fill(fVpeds[ivped], PeakADC_stdev[asics][channels][cells][ivped]);
            //if(asics==0) hRMS2[channels][cells%64]->Fill(fVpeds[ivped], PeakADC_stdev[asics][channels][cells][ivped]);
            //if(asics==0) hRMS3[channels][cells/32]->Fill(fVpeds[ivped], PeakADC_stdev[asics][channels][cells][ivped]);
          }
        }
        hTFs[asics][channels]->Write();
        delete hTFs[asics][channels];
        hRMS[asics][channels]->Write();
        delete hRMS[asics][channels];

        /*
        if(asics==0){
          for(int i=0; i<128; ++i){
            if(i<64){
              hTFs2[channels][i]->Write();
              delete hTFs2[channels][i];
              hRMS2[channels][i]->Write();
              delete hRMS2[channels][i];
            }
            hTFs3[channels][i]->Write();
            delete hTFs3[channels][i];
            hRMS3[channels][i]->Write();
            delete hRMS3[channels][i];
          }
        }*/
      }
    }
    hTFs_all->Write();
    delete hTFs_all;
    hRMS_all->Write();
    delete hRMS_all; 

    // Create TF plots and save as png files
    std::cout << "Create plots" << std::endl; 
    char graphnames[150];
    for(int asics=0; asics<ASICS; ++asics){
      for(int channels=0; channels<CHANNELS; ++channels){
        TCanvas *c1 = new TCanvas();
        TCanvas *c2 = new TCanvas();
        TGraph *g[CELLS];
        TGraph *grms[CELLS];
        for(int cells = 0; cells < CELLS; ++cells){
          // create graphs
          if(cells == 0){
            c1->cd();
            g[cells] = new TGraph(fVpeds.size(), &fVpeds[0], &PeakADC_mean[asics][channels][cells][0]);
            sprintf(graphnames,"Asic%d_Channel%d",asics,channels);
            g[cells]->SetTitle(graphnames);
            g[cells]->SetLineColor(32%9+1);
            g[cells]->Draw("APL");
            c2->cd();
            grms[cells] = new TGraph(fVpeds.size(), &fVpeds[0], &PeakADC_stdev[asics][channels][cells][0]);
            sprintf(graphnames,"Asic%d_Channel%d_noise",asics,channels);
            grms[cells]->SetTitle(graphnames);
            grms[cells]->SetLineColor(32%9+1);
            grms[cells]->GetYaxis()->SetRangeUser(0.0,50.0);
            grms[cells]->Draw("APL");
          }
          else{
            c1->cd();
            g[cells] = new TGraph(fVpeds.size(), &fVpeds[0], &PeakADC_mean[asics][channels][cells][0]);
            g[cells]->SetLineColor(cells%9+1);
            g[cells]->Draw("same");
            c2->cd();
            grms[cells] = new TGraph(fVpeds.size(), &fVpeds[0], &PeakADC_stdev[asics][channels][cells][0]);
            grms[cells]->SetLineColor(cells%9+1);
            grms[cells]->Draw("same");
          }
        }
        // Save the plots as .png files //
        sprintf(graphnames,(OutDir + "Asic%d_Channel%d.png").c_str(),asics,channels);
        c1->SaveAs(graphnames);
        c1->Write();
        sprintf(graphnames,(OutDir + "Asic%d_Channel%d_noise.png").c_str(),asics,channels);
        c2->SaveAs(graphnames);
        c2->Write();
        delete c1; delete c2;
        for (int cells = 0; cells < CELLS; ++cells){
          delete g[cells];
          delete grms[cells];
        }
      }
    }
    tfile->Close();
  }

};

int main(int argc, char** argv){

  std::cout << "Generate AC TF from data, saving it to TargetCalib format" << std::endl;

  std::string indir = "/media/cta/157bfe11-9587-4947-8a3e-1e814c5c25dc/Messungen_David/TargetC_tfs/data/";
  std::string outdir = "/media/cta/157bfe11-9587-4947-8a3e-1e814c5c25dc/Messungen_David/TargetC_tfs/new_script/";
  std::string module = "SN0022";
  bool NegMethod = true;
  bool DoBaselineCorr = true;
  bool DoPlots = true;

  // Get
  char tmp;
  while((tmp = (char) getopt(argc, argv, "hi:o:m:nbp")) != -1 ){
    switch(tmp){
      case 'h':
        ShowUsage();
        exit(0);
      case 'i':
        indir = optarg;
        break;
      case 'o':
        outdir = optarg;
        break;
      case 'm':
        module = optarg;
        break;
      case 'n':
        NegMethod = true;
        break;
      case 'b':
        DoBaselineCorr = true;
        break;
      case 'p':
        DoPlots = true;
        break;
    }
  }
  if( indir[indir.length()-1] != '/' ) indir += '/';
  if( outdir[outdir.length()-1] != '/' ) outdir += '/';

  std::cout << "Include directory: " << indir << std::endl;
  std::cout << "Output direcory: " << outdir << std::endl;
  std::cout << "Module: " << module << std::endl;
  if( NegMethod ) std::cout << "Doing special method for negative vped" << std::endl;
  if( DoBaselineCorr ) std::cout << "Doing a baseline correction" << std::endl;
  if( DoPlots ) std::cout << "Creating extra plots" << std::endl;


  // Start creation of AC transfer functions
  TFgenerator tfgenerator(indir, outdir, module, NegMethod, DoBaselineCorr, DoPlots);

  tfgenerator.GetMeanPulsePosition();
  tfgenerator.CalculateTF();
  tfgenerator.SaveTFs();
  if(DoPlots) tfgenerator.DoPlots();

}


void ShowUsage(){
  // shows the usage of this script

  std::cout << "Purpose: Create a TargetCalib AC TranserFunction file to calibrate data" << std::endl;
  std::cout << "\t and creates already some plots (if wanted)" << std::endl;
  std::cout << "Usage: generate_ac_tf [-option] [argument]" << std::endl;
  std::cout << "-h\t Show this help information" << std::endl;
  std::cout << "-i\t Input directory" << std::endl;
  std::cout << "-o\t Output directory" << std::endl;
  std::cout << "-n\t Use a special method for negative vped" << std::endl;
  std::cout << "-b\t Do a baseline correction" << std::endl;
  std::cout << "-p\t Create extra plots" << std::endl;
}
