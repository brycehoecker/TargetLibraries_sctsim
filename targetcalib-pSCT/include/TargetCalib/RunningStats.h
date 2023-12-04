// Copyright (c) 2016 The CTA Consortium. All rights reserved.
/*! \file */
/*!
 @file
 @brief Contains utility functions used by the calibration library
 */
#pragma clang diagnostic push
#pragma ide diagnostic ignored "OCUnusedStructInspection"
#pragma ide diagnostic ignored "OCUnusedGlobalDeclarationInspection"
#ifndef TARGETCALIB_RUNNINGSTATS_H
#define TARGETCALIB_RUNNINGSTATS_H

#include <cmath>

class RunningStats
{
public:
  RunningStats() :
    m_n(0),
    m_oldM(0),
    m_oldS(0),
    m_newM(0),
    m_newS(0)
  {}

  void Clear()
  {
    m_n = 0;
  }

  void Push(double x)
  {
    m_n++;

    // See Knuth TAOCP vol 2, 3rd edition, page 232
    if (m_n == 1)
    {
      m_oldM = m_newM = x;
      m_oldS = 0.0;
    }
    else
    {
      m_newM = m_oldM + (x - m_oldM)/m_n;
      m_newS = m_oldS + (x - m_oldM)*(x - m_newM);

      // set up for next iteration
      m_oldM = m_newM;
      m_oldS = m_newS;
    }
  }

  void PushArray(double* array, size_t array_size) {
    for (size_t i=0; i<array_size; ++i) {
      Push(array[i]);
    }
  }

  int NumDataValues() const
  {
    return m_n;
  }

  double Mean() const
  {
    return (m_n > 0) ? m_newM : 0.0;
  }

  double Variance() const
  {
    return ( (m_n > 1) ? m_newS/(m_n - 1) : 0.0 );
  }

  double StandardDeviation() const
  {
    return sqrt( Variance() );
  }

private:
  int m_n;
  double m_oldM, m_newM, m_oldS, m_newS;
};

#endif //TARGETCALIB_RUNNINGSTATS_H

#pragma clang diagnostic pop