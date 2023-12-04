//// Copyright (c) 2016 The CTA Consortium. All rights reserved.
///*! \file */
///*!
// @file
// @brief Executable to test the TargetCalib library
//
//
//ToDo
//- Logging
//- Consistency of Error messages
//- Tests:
//--- Memory leaks, write, read x 1000, time and average
//
// */
//
//#include "TargetCalib/Logger.h"
//#include "TargetCalib/PedestalMaker.h"
//#include "TargetCalib/TfMaker.h"
//#include "TargetCalib/Calibrator.h"
//
////TargetDriver -- Not used
////#include "TargetDriver/Waveform.h"
////#include "TargetDriver/EventHeader.h"
////#include "TargetDriver/DataPacket.h"
////#include "TargetDriver/RawEvent.h"
//
//#include <unistd.h>
//#include <iostream>
//#include <string>
//#include <vector>
//#include <fitsio.h>
//#include <iomanip>
//#include <map>
//#include <chrono>
//#include <random>
//
//using namespace CTA::TargetCalib;
//
//std::chrono::steady_clock::time_point t0;
//std::chrono::steady_clock::time_point t1;
//double dt;
//uint16_t vpedop = 1100;
//
//void MakeFakePedEvents(uint16_t nEv,
//                     std::vector<std::vector<std::vector<uint16_t>>> &data,
//                       std::vector<uint16_t> &fCellID, int fixed = -1) {
//
//  const size_t nTm = 32;
//  const size_t nTmpix = 64;
//  const size_t nSamples = 128;
//  const size_t nPix = nTm*nTmpix;
//  const size_t nCells = 16384;
//
//  uint16_t startCell = 0;
//  for (size_t ev=0; ev<nEv; ev++){
//    fCellID.push_back(startCell);
//    std::vector<std::vector<uint16_t>> event;
//    for (size_t tm=0; tm<nTm; tm++){
//      for (size_t tmpix=0; tmpix<nTmpix; tmpix++){
//        std::vector<uint16_t> wf;
//        for (size_t isam=0; isam<nSamples; isam++){
//          uint16_t val = (uint16_t)((float)(tm*nTmpix*nSamples + tmpix*nSamples + isam))/4.0;
//          if (fixed>-1) val = fixed;
//          wf.push_back(val);
//        }
//        event.push_back(wf);
//      }
//    }
//    data.push_back(event);
//    startCell += nSamples;
//    if (startCell>nCells) startCell -= nCells;
//  }
//}
//
//void MakeFakePedEvents2(uint16_t nEv,
//                        std::vector<std::vector<std::vector<uint16_t>>> &data,
//                        std::vector<uint16_t> &fCellID, int fixed = -1) {
//
//  const size_t nTm = 32;
//  const size_t nTmpix = 64;
//  const size_t nSamples = 128;
//  const size_t nPix = nTm*nTmpix;
//  const size_t nCells = 16384;
//
//  uint16_t startCell = 0;
//  for (size_t ev=0; ev<nEv; ev++){
//    fCellID.push_back(startCell);
//    std::vector<std::vector<uint16_t>> event;
//    for (size_t tm=0; tm<nTm; tm++){
//      for (size_t tmpix=0; tmpix<nTmpix; tmpix++){
//        std::vector<uint16_t> wf;
//        for (size_t isam=0; isam<nSamples; isam++){
//
//          uint16_t cell = startCell + isam;
//          uint16_t val = cell%nCells;
//          val += (ev/128);
//          if (fixed>-1) val = fixed;
//
//          wf.push_back(val);
//        }
//        event.push_back(wf);
//      }
//    }
//    data.push_back(event);
//    startCell += nSamples;
//    if (startCell>nCells) startCell -= nCells;
//  }
//}
//
//
//void MakeFakeTfEvents(uint16_t nEv,
//                      std::vector<std::vector<std::vector<std::vector<uint16_t>>>> &data,
//                      std::vector<uint16_t> &fCellID) {
//
//  // Assume these are pedestal subtracted and ready to be added to the TF maker
//  const size_t nTm = 32;
//  const size_t nTmpix = 64;
//  const size_t nSamples = 128;
//  const size_t nPix = nTm*nTmpix;
//  const size_t nCells = 64;
//  const size_t nPnts = 10;
//
//  for (size_t ivped=0; ivped<nPnts; ivped++){
//
//    uint16_t vped = 28 + ivped*(4000/nPnts);
//    //std::cout << "  ivped=" << ivped << " vped = " << vped << std::endl;
//    uint16_t adc = vped;
//    uint16_t startCell = 0;
//    std::vector<std::vector<std::vector<uint16_t>>> event_vped;
//    for (size_t ev=0; ev<nEv; ev++){
//      if (ivped==0) fCellID.push_back(startCell);
//      std::vector<std::vector<uint16_t>> event;
//      for (size_t tm=0; tm<nTm; tm++){
//        for (size_t tmpix=0; tmpix<nTmpix; tmpix++){
//          std::vector<uint16_t> wf;
//          for (size_t isam=0; isam<nSamples; isam++){
//            wf.push_back(adc);
//          }
//          event.push_back(wf);
//        }
//      }
//      event_vped.push_back(event);
//      //startCell ++;
//      //if (startCell>nCells) startCell -= nCells;
//    }
//    data.push_back(event_vped);
//  }
//}
//
//void TestPedMaker(std::string fileName,int fixedp = -1) {
//
//  std::cout << "Pedestal Generation" << std::endl;
//  const size_t nEvents = 128*2;
//  std::vector<std::vector<std::vector<uint16_t>>> r0;
//  std::vector<uint16_t> fCellID;
//  MakeFakePedEvents2(nEvents, r0, fCellID, fixedp);
//
//  CTA::TargetCalib::PedestalMaker *ped = new CTA::TargetCalib::PedestalMaker(true);
//
//  t0 = std::chrono::steady_clock::now();
//  for (size_t ev=0; ev<r0.size(); ev++)
//    for (size_t pix=0; pix<r0[0].size(); pix++)
//      for (size_t sam=0; sam<r0[0][0].size(); sam++) {
//        //if ((pix/64==0) && (pix%64==0) && (fCellID[ev]+sam)==120) std::cout << "ev=" << ev
//        //                                             << " pix/64=" << pix/64 << " pix%64=" << pix%64 << " "
//        //                      << fCellID[ev]+sam << " " << r0[ev][pix][sam] << std::endl;
//        //if (!ped->Add(pix/64, pix%64, fCellID[ev]+sam, r0[ev][pix][sam]))
//        //  std::cout << "PROBLEM tm=" << pix/64 << " tmpix=" << pix%64
//        //            << " ev=" << ev << " cell=" << fCellID[ev]+sam << " fc=" << fCellID[ev] << " sam=" << sam
//        //            << std::endl;
//      }
//
//  t1 = std::chrono::steady_clock::now();
//  dt = std::chrono::duration_cast<std::chrono::nanoseconds> (t1-t0).count();
//  std::cout << "---> Time to generate content: " << dt * 1e-6 << " ms ("
//            << nEvents << " events)" << std::endl;
//  std::cout << "---> Time to generate content per event: "
//            << dt/nEvents << " ms (" << nEvents*1e9/dt
//            << " Hz)" << std::endl;
//
//  t0 = std::chrono::steady_clock::now();
//  ped->Save(fileName, false);
//  t1 = std::chrono::steady_clock::now();
//  dt = std::chrono::duration_cast<std::chrono::nanoseconds> (t1-t0).count();
//  std::cout << "---> Time to save file: " << dt * 1e-6 << " ms" << std::endl;
//
//  std::string cFileName = fileName.substr(0,fileName.find_last_of("."));
//  cFileName.append("_compressed.tcal");
//  ped->Save(cFileName, true);
//
//
//  std::string diagnosticsFileName = "ped_diagnostics.txt";
//  std::cout << "Writing diagnostics file: " << diagnosticsFileName << std::endl;
//  std::ofstream diagnosticsFile;
//  diagnosticsFile.open (diagnosticsFileName);
//  ped->PrintDiagnostics(diagnosticsFile);
//}
//
//void TestTFMaker(std::string fileName) {
//
//  std::cout << "TF Generation" << std::endl;
//  const size_t nEvents = 10;
//  std::vector<std::vector<std::vector<std::vector<uint16_t>>>> r0;
//  std::vector<uint16_t> fCellID;
//  MakeFakeTfEvents(nEvents, r0, fCellID);
//
//  uint16_t vped[r0.size()];
//  for (size_t v=0; v<r0.size(); v++) {
//    vped[v] = r0[v][0][0][0];
//  }
//  CTA::TargetCalib::TfMaker *tf = new CTA::TargetCalib::TfMaker(vped, r0.size());
//
//  t0 = std::chrono::steady_clock::now();
//  for (size_t v=0; v<r0.size(); v++) {
//    if (!tf->SetVpedIndex(r0[v][0][0][0])) {
//      std::cout << "Could not set vped index for vped=" << r0[v][0][0][0] << std::endl;
//    }
//    for (size_t ev=0; ev<r0[0].size(); ev++) {
//      for (size_t pix=0; pix<r0[0][0].size(); pix++) {
//        for (size_t sam=0; sam<r0[0][0][0].size(); sam++){
//          if (!tf->Add(pix/64, pix%64, fCellID[ev]+sam, r0[v][ev][pix][sam]))
//            std::cout << "PROBLEM" << std::endl;
//        }
//      }
//    }
//  }
//  t1 = std::chrono::steady_clock::now();
//  dt = std::chrono::duration_cast<std::chrono::nanoseconds> (t1-t0).count();
//  std::cout << "---> Time to generate content: " << dt * 1e-6 << " ms ("
//            << nEvents << " events)" << std::endl;
//  std::cout << "---> Time to generate content per event: "
//            << dt/nEvents << " ms (" << nEvents*1e9/dt
//            << " Hz)" << std::endl;
//
//  t0 = std::chrono::steady_clock::now();
//  tf->Save(fileName, 11, false);
//  t1 = std::chrono::steady_clock::now();
//  dt = std::chrono::duration_cast<std::chrono::nanoseconds> (t1-t0).count();
//  std::cout << "---> Time to save file: " << dt * 1e-6 << " ms" << std::endl;
//
//  //std::string cFileName = fileName.substr(0,fileName.find_last_of("."));
//  //cFileName.append("_compressed.tcal");
//  //tf->Save(cFileName, 8, true);
//}
//
//void TestCalibratorPed(std::string fileName) {
//
//  std::cout << "Pedestal Subtraction" << std::endl;
//  const size_t nEvents = 128*2;
//  std::vector<std::vector<std::vector<uint16_t>>> r0;
//  std::vector<uint16_t> fCellID;
//  MakeFakePedEvents2(nEvents, r0, fCellID);
//
//  t0 = std::chrono::steady_clock::now();
//  CTA::TargetCalib::Calibrator *c = new CTA::TargetCalib::Calibrator(fileName);
//  t1 = std::chrono::steady_clock::now();
//  dt = std::chrono::duration_cast<std::chrono::nanoseconds> (t1-t0).count() * 1e-6;
//  std::cout << "---> Time to load file: " << dt << " ms" << std::endl;
//
//  uint32_t nBad = 0;
//
//  t0 = std::chrono::steady_clock::now();
//  for (size_t ev=0; ev<r0.size(); ev++){
//    for (size_t pix=0; pix<r0[0].size(); pix++){
//      c->SetLookupIndex(pix/64, pix%64);
//      for (size_t sam=0; sam<r0[0][0].size(); sam++){
//        float val = (float)r0[ev][pix][sam];
//        float cal = 0;//c->Apply(fCellID[ev]+sam, val);
//        if (fabs(cal)>0.50001) {
//          std::cout << "Large redidual found: "
//                    << " Event: " << ev << " TM: " << pix/64 << " Pix: " << pix%64
//                    << " Cell: " << fCellID[ev]+sam
//                    << " ADC: " << val << " Calibrated val: " << cal << std::endl;
//          nBad++;
//        }
//      }
//    }
//  }
//
//
//
//  /*c->SetLookupIndex(0, 0);
//  for (size_t sam=0; sam<r0[0][0].size(); sam++){
//    float val = (float)r0[0][0][sam];
//    float cal = c->Apply(fCellID[0]+sam, val);
//    std::cout << "      cal = " << cal << std::endl;
//    if (fabs(cal)>0.50001) {
//      std::cout << "Large redidual found: "
//                << " Event: " << 0 << " TM: " << 0 << " Pix: " << 0
//                << " Cell: " << fCellID[0]+sam
//                << " ADC: " << val << " Calibrated val: " << cal << std::endl;
//      nBad++;
//    }
//    }*/
//
//  t1 = std::chrono::steady_clock::now();
//  dt = std::chrono::duration_cast<std::chrono::nanoseconds> (t1-t0).count();
//
//  std::cout << "---> Time to apply content: " << dt << " ms ("
//              << nEvents << " events)" << std::endl;
//  std::cout << "---> Time to apply content per event: "
//            << dt/nEvents << " ms (" << nEvents*1e9/dt << " Hz)" << std::endl;
//
//  if(nBad>0)
//    std::cout << "A total of " << nBad
//              << " samples were found with incorrect values" << std::endl;
//  else
//    std::cout << "Success: pedestal corrected fake data all 0" << std::endl;
//
//  //c->PrintPed(0,0);
//}
//
//void TestCalibratorTf(std::string fileName) {
//
//  std::cout << "TF Application" << std::endl;
//  TestPedMaker("ped0.tcal", 0);
//
//  const size_t nEvents = 1;
//  std::vector<std::vector<std::vector<std::vector<uint16_t>>>> r0;
//  std::vector<uint16_t> fCellID;
//  MakeFakeTfEvents(nEvents, r0, fCellID);
//
//  t0 = std::chrono::steady_clock::now();
//  CTA::TargetCalib::Calibrator *c = new CTA::TargetCalib::Calibrator("ped0.tcal",fileName);
//  t1 = std::chrono::steady_clock::now();
//  dt = std::chrono::duration_cast<std::chrono::nanoseconds> (t1-t0).count() * 1e-6;
//  std::cout << "---> Time to load file: " << dt << " ms" << std::endl;
//
//  uint32_t nBad = 0;
//  t0 = std::chrono::steady_clock::now();
//  for (size_t v=0; v<r0.size(); v++) {
//    for (size_t ev=0; ev<r0[0].size(); ev++) {
//      for (size_t pix=0; pix<1;pix++){//r0[0][0].size(); pix++) {
//        c->SetLookupIndex(pix/64, pix%64);
//        for (size_t sam=0; sam<1; sam++){//r0[0][0][0].size(); sam++){
//          float val = (float)r0[v][ev][pix][sam];
//          float cal = 0;//c->Apply(fCellID[ev]+sam, val);
//          if (abs(cal-val)>1e-5) {
//            std::cout << "Large redidual found: "
//                      << " Event: " << ev << " TM: " << pix/64 << " Pix: " << pix%64
//                      << " Cell: " << fCellID[ev]+sam
//                      << " ADC: " << val << " Calibrated val: " << cal << std::endl;
//            nBad++;
//          }
//        }
//      }
//    }
//  }
//  t1 = std::chrono::steady_clock::now();
//  dt = std::chrono::duration_cast<std::chrono::nanoseconds> (t1-t0).count();
//
//  std::cout << "---> Time to apply content: " << dt << " ms ("
//              << nEvents << " events)" << std::endl;
//  std::cout << "---> Time to apply content per event: "
//            << dt/nEvents << " ms (" << nEvents*1e9/dt << " Hz)" << std::endl;
//
//  if(nBad>0)
//    std::cout << "A total of " << nBad
//              << " samples were found with incorrect values" << std::endl;
//  else
//    std::cout << "Success: tf corrected fake data all 0" << std::endl;
//
//  //c->PrintTf(0,0,0);
//}
//
//
//void TestCalibratorPedTf(std::string fileNamePed, std::string fileNameTf) {
//
//  std::cout << "Pedestal Subtraction and TF Application" << std::endl;
//
//  const size_t nEvents = 128*10;
//  const size_t nTm = 32;
//  const size_t nTmpix = 64;
//  const size_t nSamples = 96;
//  const size_t nPix = nTm*nTmpix;
//  const size_t nCells = 16384;
//
//  t0 = std::chrono::steady_clock::now();
//
//  CTA::TargetCalib::Calibrator *cal
//    = new CTA::TargetCalib::Calibrator(fileNamePed, fileNameTf);
//
//  t1 = std::chrono::steady_clock::now();
//  dt = std::chrono::duration_cast<std::chrono::nanoseconds> (t1-t0).count() * 1e-6;
//  std::cout << "---> Time to load file: " << dt << " ms" << std::endl;
//
//  double totaltime = 0;
//  uint16_t startCell = 0;
//  for (size_t ev=0; ev<nEvents; ev++){
//    uint16_t tmList[nPix];
//    uint16_t tmpixList[nPix];
//    uint16_t startCells[nPix];
//    uint16_t wfs[nPix*nSamples];
//    float wfsCal[nPix*nSamples];
//    for (size_t tm=0; tm<nTm; tm++){
//      for (size_t tmpix=0; tmpix<nTmpix; tmpix++){
//        size_t pix = tm*nTmpix + tmpix;
//        tmList[pix] = (uint16_t)tm;
//        tmpixList[pix] = tmpix;
//        startCells[pix] = (uint16_t)startCell;
//        for (size_t sample=0; sample<nSamples; sample++){
//          size_t i = pix*nSamples + sample;
//          int r = (rand() % 100) + 1;
//          wfs[i] = vpedop + 200;
//          wfsCal[i] = 0;
//        }
//      }
//    }
//
//    startCell += nSamples;
//    if (startCell>nCells) startCell -= nCells;
//
//    t0 = std::chrono::steady_clock::now();
//    if(!cal->ApplyEvent(tmList, nPix, tmpixList, nPix, wfs, nPix, nSamples,
//                        startCells, nPix, wfsCal, nPix, nSamples, false)) {
//      std::cout << "PROBLEM" << std::endl;
//    }
//    t1 = std::chrono::steady_clock::now();
//    dt = std::chrono::duration_cast<std::chrono::nanoseconds> (t1-t0).count() * 1e-6;
//    totaltime += dt;
//  }
//  std::cout << "---> Time to apply content: " << totaltime << " ms ("
//              << nEvents << " events)" << std::endl;
//  std::cout << "---> Time to apply content per event: "
//            << totaltime/nEvents << " ms (" << nEvents*1000/totaltime << " Hz)" << std::endl;
//
//}
//
//
//int main(int argc, char** argv) {
//
//  //FLog().ReportingLevel() = sDebugVerbose;
//  FLog().ReportingLevel() = sDebug;
//  //FLog().ReportingLevel() = sWarning;
//
//  // Ped
//  std::string fileNamePed = "testPed.fits";
//  //TestPedMaker(fileNamePed);
//  //TestCalibratorPed(fileNamePed);
//
//  // TF
//  //std::string fileNameTf = "testTf.fits";
//  //TestTFMaker(fileNameTf);
//  //TestCalibratorTf(fileNameTf);
//
//  //TestCalibratorPedTf(fileNamePed, fileNameTf);
//  /*
//  std::vector<std::vector<std::vector<std::vector<float>>>> ped;
//  for (size_t tm=0; tm<32; ++tm){
//    std::vector<std::vector<std::vector<float>>> pedA;
//    for (size_t tmpix=0; tmpix<64; ++tmpix){
//      std::vector<std::vector<float>> pedB;
//      for (size_t cell=0; cell<16384; ++cell) {
//         std::vector<float> pedC;
//         for (size_t blk=0; blk<4; ++blk) {
//           pedC.push_back(99);
//         }
//         pedB.push_back(pedC);
//      }
//      pedA.push_back(pedB);
//    }
//    ped.push_back(pedA);
//    std::cout << "TM=" << tm << std::endl;
//    }*/
//
//  //std::vector<std::vector<std::vector<std::vector<float>>>> pixV(32,
//  //                                                               std::vector<std::vector<std::vector<float>>>(64,
//  //                                                               std::vector<std::vector<float>>(16384,
//  //                                                                                               std::vector<float>(4, 0.0))));
//
//  /*
//  std::vector<std::vector<std::vector<float>>> pixV(64,std::vector<std::vector<float>>(16384,
//                                                                                       std::vector<float>(4, 80.0)));
//
//
//  std::vector<std::vector<std::vector<std::vector<float>>>> a;
//
//  a.resize(32, pixV);
//  std::cout << "a=" << a[0][0][0][0] << std::endl;
//  */
//
//  CTA::TargetCalib::PedestalMaker *ped =
//    new CTA::TargetCalib::PedestalMaker(false,4,32);
//
//  return 0;
//
//}
