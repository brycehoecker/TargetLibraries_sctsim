// Copyright (c) 2015 The CTA Consortium. All rights reserved.
#include "TargetDriver/ModuleSimulator.h"

#include <arpa/inet.h>
#include <math.h>
#include <string.h>
#include <unistd.h>
#include <iostream>
#include <vector>
namespace CTA {
namespace TargetDriver {

ModuleSimulator::ModuleSimulator(const std::string& pModuleIP,
                                 const std::string& pFPGADef,
                                 const std::string& pASICDef,
                                 const std::string& pTriggerASICDef,
                                 double pRate)
    : UDPServer(pModuleIP, TM_DEST_PORT, TM_DAQ_PORT, TM_RESPONSE_TIME_OUT),
      fVerbose(false),
      fRunning(false),
      fTargetSettings(pFPGADef, pASICDef, pTriggerASICDef),
      fTriggerTimeIntervalUs(1e9),
      fWaveformsPerPacket(0),
      fNumberOfBuffers(0),
      fTriggering(false),
      fEventNumber(uint64_t(random())),
      fDataPacket(NULL),
      fTriggerCounter(0)

{
  SetTriggerRate(pRate);
}

void ModuleSimulator::ListenAndRespond() {
  uint8_t mesg[100];  // allow for somewhat larger than expected packets
  ssize_t nbytes = 0;
  int loops = 0;

  uint32_t resetAddress =
      fTargetSettings.fSettingMapFPGA.find("SoftwareReset")->second.regAddr;

  while (fRunning) {
    // check for messages
    nbytes = 0;
    int stat = Receive(mesg, nbytes, 100);
    if (nbytes > 0 && stat == TC_OK) {
      if (nbytes != TM_CONTROLPACKET_SIZE) {
        std::cout << "ModuleSimulator::ListenAndRespond() - Wrong packet size: "
                  << nbytes << " ignoring " << std::endl;
        continue;
      }

      uint32_t addr, data;
      bool iswrite;
      bool stop_trigger = false;
      TargetModule::UnpackControlPacket(mesg, addr, data, iswrite);
      if (iswrite) {
        if (fVerbose) {
          std::cout << "ModuleSimulator::ListenAndRespond() - Writing: "
                    << std::hex << data << " to addr: 0x" << addr << std::endl;
        }
        fTargetSettings.fRegisterMapFPGA[addr].val = data;
        // if register 0x17 we have to do some stuff
        // check if number of waveforms per packet changed
        if (addr == 0x17) {
          if (data & 1) {
            std::cout << "Tried to write Enable bit..." << std::endl;
          } else {
            stop_trigger = true;
          }

          // getting the number of waveforms per packet
          auto it = fTargetSettings.fSettingMapFPGA.find("MaxChannelsInPacket");
          fWaveformsPerPacket = 0;
          if (it == fTargetSettings.fSettingMapFPGA.end()) {
            std::cerr << "Warning, cannot find MaxChannelsInPacket in FPGA "
                         "definition file, cannot set the number of event per "
                         "packet"
                      << std::endl;
          } else {
            uint32_t val;
            fTargetSettings.GetRegisterPartially(data, it->second, val);
            fWaveformsPerPacket = (uint8_t)val;
            if (fWaveformsPerPacket == 0) fWaveformsPerPacket = 1;
          }

        } else if (addr == 0x1C) {
          // if register is 0x1C, the number of buffers might have changed
          auto it = fTargetSettings.fSettingMapFPGA.find("NumberOfBlocks");
          fNumberOfBuffers = 0;
          uint32_t val;
          fTargetSettings.GetRegisterPartially(data, it->second, val);
          fNumberOfBuffers = (uint8_t)val;
          fNumberOfBuffers++;

          std::cout << "changing number of buffers to " << fNumberOfBuffers
                    << std::endl;

          SetRefWaveform();
        } else if (addr == 0x01) {
          stop_trigger = true;  // Writing the module index etc - assumed to be
                                // in GoToSafe... Jim
        } else if (addr == resetAddress) {
          // In a real module the FPGA logic will be reset but register settings
          // are kept. No response is sent from the FPGA.
          usleep(500);
          ++loops;
          continue;
        }
      } else {  // THIS WAS A READ COMMAND

        if (fVerbose)
          std::cout << "ModuleSimulator::ListenAndRespond() - Reading from "
                    << addr << std::endl;

        if (fTargetSettings.fRegisterMapFPGA.find(addr) !=
            fTargetSettings.fRegisterMapFPGA.end()) {
          data = fTargetSettings.fRegisterMapFPGA[addr].val;
        } else
          data = 0;

        if (addr == 0x17) {
          std::cout << "Someone read register 0x17 so we start triggering..."
                    << std::endl;
          StartTriggering();
          data |= 1;
          //	    std::cout << " data " << data <<" masked " << (data & 0x1)
          //<< std::endl;
        }
      }

      TargetModule::PackControlPacket(mesg, addr, data, false);
      SendResponse(mesg, TM_CONTROLPACKET_SIZE);
      if (fVerbose)
        std::cout << "ModuleSimulator::ListenAndRespond() - sent response "
                  << addr << " " << data << std::endl;

      //          if (stop_trigger) StopTriggering();
    }

    usleep(500);
    ++loops;
    if ((loops % 1000) == 0)
      std::cout << "listening loops: " << std::dec << loops << std::endl;
    // std::cout << "loops: "  std::dec << loops << std::endl;
  }
}

void ModuleSimulator::RunTrigger() {
  /// trigger
  if (fVerbose) std::cout << "Start RunTrigger " << std::endl;
  while (fTriggering) {
    if (CheckTimeDifference()) {
      gettimeofday(&fRefTime, NULL);
      SendEventData();
      fTriggerCounter++;
    };
  }
  std::cout << "Triggering finished" << std::endl;
}

void ModuleSimulator::Start() {
  if (IsRunning()) {
    return;
  }

  fRunning = true;
  fThreadControl = std::thread(&ModuleSimulator::ListenAndRespond, this);
}

void ModuleSimulator::Stop() {
  std::cout << "The ModuleSimulator generated " << fTriggerCounter
            << " triggers" << std::endl;

  StopTriggering();

  if (!IsRunning()) {
    return;
  }

  fRunning = false;

  // Jim - no need to block here while trigger thread finishes
  // Harm - code breaks if we don't have these lines here..
  if (fThreadControl.joinable()) {
    fThreadControl.join();
  }
}

void ModuleSimulator::StartTriggering() {
  if (fTriggering) {
    if (fVerbose) std::cout << "we are already triggering" << std::endl;
    return;
  }
  fTriggering = true;
  fEventNumber = 0;
  gettimeofday(&fRefTime, NULL);

  fRefTime.tv_sec += 1;  // add a second so rest of the registers can be updated
  fStartRefTime = fRefTime;
  if (fVerbose) {
    std::cout << "Started triggering..." << std::endl;
  }
  fThreadTriggering = std::thread(&ModuleSimulator::RunTrigger, this);
  if (fVerbose) {
    std::cout << "Generate trigger thread..." << std::endl;
  }
}

void ModuleSimulator::StopTriggering() {
  if (!fTriggering) {
    return;
  }
  fTriggering = false;

  // Jim - no need to block here while trigger thread finishes
  // Harm - code breaks if we dont have these lines here
  if (fThreadTriggering.joinable()) {
    fThreadTriggering.join();
  }

  struct timeval ctv;
  gettimeofday(&ctv, NULL);

  time_t dseconds = ctv.tv_sec - fStartRefTime.tv_sec;
  suseconds_t dus = ctv.tv_usec - fStartRefTime.tv_usec;

  double dt = dseconds + double(dus) * 1e-6;
  if (fVerbose) {
    std::cout << "Stopped triggering..." << std::endl;
    std::cout << "dt " << dt << std::endl;
    std::cout << "fTriggerCounter " << fTriggerCounter << std::endl;
    std::cout << "Rate " << fTriggerCounter / dt << std::endl;
  }
}

void ModuleSimulator::SetTriggerRate(double pRate) {
  if (pRate > 0) {
    fTriggerTimeIntervalUs = (uint32_t)(1.e6 / pRate);
  } else {
    std::cerr << "Error: ModuleSimulator::SetTriggerRate(val), val should be "
                 "larger than 0 "
              << std::endl;
  }
  if (fVerbose) {
    std::cout << "Trigger Rate: " << pRate << std::endl;
    std::cout << "fTriggerTimeIntervalUs:  " << fTriggerTimeIntervalUs
              << std::endl;
  }
}

bool ModuleSimulator::CheckTimeDifference() {
  if (!fTriggering) {
    return false;
  }

  struct timeval ctv;
  gettimeofday(&ctv, NULL);
  //  if (ctv.tv_sec < fRefTime.tv_sec)
  //    return false;

  time_t dseconds = ctv.tv_sec - fRefTime.tv_sec;
  suseconds_t dus = ctv.tv_usec - fRefTime.tv_usec;

  double dt = (dseconds * 1.0e6 + dus * 1.0);

  double left_to_sleep = (fTriggerTimeIntervalUs - dt);

  if (left_to_sleep > 1000) {
    usleep(useconds_t(0.8 * left_to_sleep));
  }
  return left_to_sleep < 0;
}

void ModuleSimulator::SendEventData() {
  if (fDataPacket == NULL) {
    if (fVerbose) std::cout << "fDataPacket == NULL" << std::endl;
    return;
  }

  uint64_t tack = fEventNumber;
  uint8_t slotID = 0;
  uint8_t detectorID = 0;

  // TODO: Slot and detector ID should be extracted from Register Map

  uint8_t eventSequenceNumber = 0;
  uint8_t quad = 0;
  uint8_t row = 0;
  uint8_t col = 0;

  uint16_t nSamples = fNumberOfBuffers * 32;

  //  // packetID =
  //  (detectorID[0-255]*64+asic[0-3]*16+ch[0-15])/kNWavesPerPacket
  //
  uint8_t cnt = 0;
  uint8_t nPack = TM_PIXELS_PER_MODULE / fWaveformsPerPacket;
  for (uint8_t iPack = 0; iPack < nPack; iPack++) {
    //    eventSequenceNumber = iPack;
    eventSequenceNumber = 0;
    fDataPacket->FillHeader(fWaveformsPerPacket, nSamples, slotID, detectorID,
                            eventSequenceNumber, tack, quad, row, col);

    Waveform* w = fDataPacket->GetWaveform(0);

    for (uint8_t iWav = 0; iWav < fWaveformsPerPacket; ++iWav) {
      uint8_t asic = cnt / TM_PIXELS_PER_ASIC;
      uint8_t channel = cnt - (asic * TM_PIXELS_PER_ASIC);
      w->SetHeader(asic, channel, nSamples, false);
      cnt++;
    }

    if (fVerbose) {
      std::cout << "Send data packet: event: " << fEventNumber << "\t packet "
                << int(iPack) << "\t size: " << fDataPacket->GetPacketSize()
                << "\t num. waveforms: "
                << fDataPacket->GetNumberOfWaveforms();  // << std::endl;
      std::cout << "\t nSamples: " << nSamples;          // << std::endl;
      uint16_t packId = 0;
      if (!fDataPacket->GetPacketID(packId))
        std::cout << " problem extracting packet ID " << std::endl;
      std::cout << " packetID: " << packId;  // << std::endl;
      w = fDataPacket->GetWaveform(0);
      uint8_t asic = w->GetASIC();
      uint8_t chan = w->GetChannel();
      uint8_t module = fDataPacket->GetDetectorID();
      std::cout << "asic: " << int(asic);   // << std::endl;
      std::cout << " chan: " << (int)chan;  // << std::endl;
      std::cout << " module: " << (int)module << std::endl;

      //      fDataPacket->Print();
    }

    SendDataPacket(fDataPacket->GetData(), fDataPacket->GetPacketSize());
    delete w;
  }
  fEventNumber++;
}

void ModuleSimulator::SetRefWaveform() {
  if (fVerbose) {
    std::cout << " Set reference waveform " << std::endl;
  }
  uint64_t tack = fEventNumber;
  uint8_t slotID = 0;
  uint8_t detectorID = 0;
  uint8_t quad = 1;
  uint8_t row = 2;
  uint8_t col = 3;

  if (fNumberOfBuffers != 0) {
    uint8_t eventSequenceNumber = 0;
    uint8_t nPack = 64 / fWaveformsPerPacket;
    uint16_t nSamples = fNumberOfBuffers * 32;
    fRefWaveforms.clear();
    uint16_t* waveform = NULL;
    if (fVerbose) {
      std::cout << " nSamples  " << std::dec << nSamples
                << "\tfNumberOfBuffers: " << fNumberOfBuffers << std::endl;
    }
    for (uint32_t iWav = 0; iWav < fWaveformsPerPacket; iWav++) {
      waveform = new uint16_t[nSamples];
      for (uint8_t iSam = 0; iSam < nSamples; iSam++) {
        waveform[iSam] = 100;
        if (iSam > 10 + iWav)
          waveform[iSam] += (uint16_t)(50 * exp(-0.1 * (iSam - 10 - iWav)));
        // if (fVerbose) {
        //   std::cout << std::dec << int(iSam) << "\t" << waveform[iSam] <<
        //   std::endl;
        // }
      }
      fRefWaveforms.push_back(waveform);
    }

    // data packet stuff
    fDataPacket = new DataPacket(fWaveformsPerPacket, nSamples);
    uint8_t cnt = 0;
    for (uint8_t iPack = 0; iPack < nPack; iPack++) {
      eventSequenceNumber = iPack;
      fDataPacket->FillHeader(fWaveformsPerPacket, nSamples, slotID, detectorID,
                              eventSequenceNumber, tack, quad, row, col);
      fDataPacket->FillFooter();
      for (uint8_t iWav = 0; iWav < fWaveformsPerPacket; ++iWav) {
        CTA::TargetDriver::Waveform* waveform = fDataPacket->GetWaveform(iWav);
        uint8_t asic = cnt / 16;
        uint8_t channel = cnt - (asic * 16);
        if (fVerbose) {
          //          std::cout << "addr ptr= " << std::dec <<
          //          fRefWaveforms[iWav] << std::endl;
          std::cout << "nSamples = " << std::dec
                    << nSamples;  // << std::endl;
                                  //    std::cout << " fRefWaveforms.size = " <<
                                  //    std::dec << fRefWaveforms.size() <<
                                  //    std::endl;
          std::cout << " fWaveformsPerPacket = " << std::dec
                    << fWaveformsPerPacket;                     // << std::endl;
          std::cout << " asic = " << std::dec << int(asic);     // << std::endl;
          std::cout << " chan = " << std::dec << int(channel);  // << std::endl;
          std::cout << " cnt = " << std::dec << int(cnt) << std::endl;
        }
        if (fRefWaveforms.size() != 0) {
          waveform->PackWaveform(asic, channel, nSamples, false,
                                 fRefWaveforms[iWav]);
          //          waveform->PackWaveform( asic, iWav, nSamples,false);
        } else {
          if (fVerbose) {
            std::cout << "WARNING: No reference waveform set " << std::endl;
          }
          waveform->PackWaveform(asic, iWav, nSamples, false);
        }
        cnt++;
      }
    }
  }
}

}  // namespace TargetDriver
}  // namespace CTA
