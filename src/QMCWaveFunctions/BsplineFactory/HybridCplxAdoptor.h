//////////////////////////////////////////////////////////////////////////////////////
// This file is distributed under the University of Illinois/NCSA Open Source License.
// See LICENSE file in top directory for details.
//
// Copyright (c) 2016 Jeongnim Kim and QMCPACK developers.
//
// File developed by: Ye Luo, yeluo@anl.gov, Argonne National Laboratory
//
// File created by: Ye Luo, yeluo@anl.gov, Argonne National Laboratory
//
//////////////////////////////////////////////////////////////////////////////////////


/** @file HybridCplxAdoptor.h
 *
 * Adoptor classes to handle complex hybrid orbitals with arbitrary precision
 */
#ifndef QMCPLUSPLUS_HYBRID_CPLX_SOA_ADOPTOR_H
#define QMCPLUSPLUS_HYBRID_CPLX_SOA_ADOPTOR_H

#include <QMCWaveFunctions/BsplineFactory/HybridAdoptorBase.h>
namespace qmcplusplus
{
/** adoptor class to match
 *
 */
template<typename BaseAdoptor>
struct HybridCplxSoA : public BaseAdoptor, public HybridAdoptorBase<typename BaseAdoptor::DataType>
{
  using HybridBase       = HybridAdoptorBase<typename BaseAdoptor::DataType>;
  using ST               = typename BaseAdoptor::DataType;
  using PointType        = typename BaseAdoptor::PointType;
  using SingleSplineType = typename BaseAdoptor::SingleSplineType;
  using RealType         = typename BaseAdoptor::RealType;
  // types for evaluation results
  using typename BaseAdoptor::GGGVector_t;
  using typename BaseAdoptor::GradVector_t;
  using typename BaseAdoptor::HessVector_t;
  using typename BaseAdoptor::ValueType;
  using typename BaseAdoptor::ValueVector_t;

  ValueVector_t psi_AO, d2psi_AO;
  GradVector_t dpsi_AO;
  Matrix<ST, aligned_allocator<ST>> multi_myV;

  using BaseAdoptor::myG;
  using BaseAdoptor::myH;
  using BaseAdoptor::myL;
  using BaseAdoptor::myV;
  using HybridBase::d2f_dr2;
  using HybridBase::df_dr;
  using HybridBase::dist_dr;
  using HybridBase::dist_r;

  HybridCplxSoA()
  {
    this->AdoptorName = "Hybrid" + this->AdoptorName;
    this->KeyWord     = "Hybrid" + this->KeyWord;
  }

  virtual SPOSet* makeClone() const override { return new HybridCplxSoA(*this); }

  inline void resizeStorage(size_t n, size_t nvals)
  {
    BaseAdoptor::resizeStorage(n, nvals);
    HybridBase::resizeStorage(myV.size());
  }

  void bcast_tables(Communicate* comm)
  {
    BaseAdoptor::bcast_tables(comm);
    HybridBase::bcast_tables(comm);
  }

  void gather_tables(Communicate* comm)
  {
    BaseAdoptor::gather_tables(comm);
    HybridBase::gather_atomic_tables(comm, BaseAdoptor::offset);
  }

  bool read_splines(hdf_archive& h5f) { return HybridBase::read_splines(h5f) && BaseAdoptor::read_splines(h5f); }

  bool write_splines(hdf_archive& h5f) { return HybridBase::write_splines(h5f) && BaseAdoptor::write_splines(h5f); }

  inline void flush_zero()
  {
    //BaseAdoptor::flush_zero();
    HybridBase::flush_zero();
  }

  void evaluateValue(const ParticleSet& P, const int iat, ValueVector_t& psi) override
  {
    const RealType smooth_factor = HybridBase::evaluate_v(P, iat, myV);
    const RealType cone(1);
    if (smooth_factor < 0)
    {
      BaseAdoptor::evaluateValue(P, iat, psi);
    }
    else if (smooth_factor == cone)
    {
      const PointType& r = P.activeR(iat);
      BaseAdoptor::assign_v(r, myV, psi, 0, myV.size() / 2);
    }
    else
    {
      const PointType& r = P.activeR(iat);
      psi_AO.resize(psi.size());
      BaseAdoptor::assign_v(r, myV, psi_AO, 0, myV.size() / 2);
      BaseAdoptor::evaluateValue(P, iat, psi);
      HybridBase::interpolate_buffer_v(psi, psi_AO);
    }
  }


  void evaluateDetRatios(const VirtualParticleSet& VP,
                         ValueVector_t& psi,
                         const ValueVector_t& psiinv,
                         std::vector<ValueType>& ratios) override
  {
    if (VP.isOnSphere())
    {
      // resize scratch space
      psi_AO.resize(psi.size());
      if (multi_myV.rows() < VP.getTotalNum())
        multi_myV.resize(VP.getTotalNum(), myV.size());
      const RealType smooth_factor = HybridBase::evaluateValuesC2X(VP, multi_myV);
      const RealType cone(1);
      for (int iat = 0; iat < VP.getTotalNum(); ++iat)
      {
        if (smooth_factor < 0)
          BaseAdoptor::evaluateValue(VP, iat, psi);
        else if (smooth_factor == cone)
        {
          const PointType& r = VP.R[iat];
          Vector<ST, aligned_allocator<ST>> myV_one(multi_myV[iat], myV.size());
          BaseAdoptor::assign_v(r, myV_one, psi, 0, myV.size() / 2);
        }
        else
        {
          const PointType& r = VP.R[iat];
          Vector<ST, aligned_allocator<ST>> myV_one(multi_myV[iat], myV.size());
          BaseAdoptor::assign_v(r, myV_one, psi_AO, 0, myV.size() / 2);
          BaseAdoptor::evaluateValue(VP, iat, psi);
          HybridBase::interpolate_buffer_v(psi, psi_AO);
        }
        ratios[iat] = simd::dot(psi.data(), psiinv.data(), psi.size());
      }
    }
    else
    {
      for (int iat = 0; iat < VP.getTotalNum(); ++iat)
      {
        evaluateValue(VP, iat, psi);
        ratios[iat] = simd::dot(psi.data(), psiinv.data(), psi.size());
      }
    }
  }

  void evaluateVGL(const ParticleSet& P,
                   const int iat,
                   ValueVector_t& psi,
                   GradVector_t& dpsi,
                   ValueVector_t& d2psi) override
  {
    const RealType smooth_factor = HybridBase::evaluate_vgl(P, iat, myV, myG, myL);
    const RealType cone(1);
    if (smooth_factor < 0)
    {
      BaseAdoptor::evaluateVGL(P, iat, psi, dpsi, d2psi);
    }
    else if (smooth_factor == cone)
    {
      const PointType& r = P.activeR(iat);
      BaseAdoptor::assign_vgl_from_l(r, psi, dpsi, d2psi);
    }
    else
    {
      const PointType& r = P.activeR(iat);
      psi_AO.resize(psi.size());
      dpsi_AO.resize(psi.size());
      d2psi_AO.resize(psi.size());
      BaseAdoptor::assign_vgl_from_l(r, psi_AO, dpsi_AO, d2psi_AO);
      BaseAdoptor::evaluateVGL(P, iat, psi, dpsi, d2psi);
      HybridBase::interpolate_buffer_vgl(psi, dpsi, d2psi, psi_AO, dpsi_AO, d2psi_AO);
    }
  }

  void evaluateVGH(const ParticleSet& P,
                   const int iat,
                   ValueVector_t& psi,
                   GradVector_t& dpsi,
                   HessVector_t& grad_grad_psi) override
  {
    APP_ABORT("HybridCplxSoA::evaluate_vgh not implemented!");
    if (HybridBase::evaluate_vgh(P, iat, myV, myG, myH))
    {
      const PointType& r = P.activeR(iat);
      BaseAdoptor::assign_vgh(r, psi, dpsi, grad_grad_psi, 0, myV.size() / 2);
    }
    else
      BaseAdoptor::evaluateVGH(P, iat, psi, dpsi, grad_grad_psi);
  }

  void evaluateVGHGH(const ParticleSet& P,
                     const int iat,
                     ValueVector_t& psi,
                     GradVector_t& dpsi,
                     HessVector_t& grad_grad_psi,
                     GGGVector_t& grad_grad_grad_psi) override
  {
    APP_ABORT("HybridCplxSoA::evaluate_vghgh not implemented!");
  }
};

} // namespace qmcplusplus
#endif
