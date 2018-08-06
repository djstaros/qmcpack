//////////////////////////////////////////////////////////////////////////////////////
// This file is distributed under the University of Illinois/NCSA Open Source License.
// See LICENSE file in top directory for details.
//
// Copyright (c) 2016 Jeongnim Kim and QMCPACK developers.
//
// File developed by: Raymond Clay III, j.k.rofling@gmail.com, Lawrence Livermore National Laboratory
//
// File created by: Raymond Clay III, j.k.rofling@gmail.com, Lawrence Livermore National Laboratory
//////////////////////////////////////////////////////////////////////////////////////
    
    



#include <LongRange/EwaldHandler3D.h>

namespace qmcplusplus
{
void EwaldHandler3D::initBreakup(ParticleSet& ref)
{
  SuperCellEnum=ref.Lattice.SuperCellEnum;
  LR_rc=ref.Lattice.LR_rc;
  LR_kc=ref.Lattice.LR_kc;
  Sigma=3.5;
  //determine the sigma
  while(erfc(Sigma)/LR_rc>1e-10)
  {
    Sigma+=0.1;
  }
  app_log() << "   EwaldHandler3D Sigma/LR_rc = " << Sigma ;
  Sigma/=ref.Lattice.LR_rc;
  app_log() << "  Sigma=" << Sigma  << std::endl;
  Volume=ref.Lattice.Volume;
  PreFactors=0.0;
  fillFk(ref.SK->KLists);
  fillYkgstrain(ref.SK->KLists);
  filldFk_dk(ref.SK->KLists);
}

EwaldHandler3D::EwaldHandler3D(const EwaldHandler3D& aLR, ParticleSet& ref):
  LRHandlerBase(aLR), Sigma(aLR.Sigma), Volume(aLR.Volume), Area(aLR.Area)
  , PreFactors(aLR.PreFactors)
{
  SuperCellEnum = aLR.SuperCellEnum;
}

void EwaldHandler3D::fillFk(KContainer& KList)
{
  Fk.resize(KList.kpts_cart.size());
  Fkg.resize(KList.kpts_cart.size());
  Fkgstrain.resize(KList.kpts_cart.size());
  const std::vector<int>& kshell(KList.kshell);
  
  if(MaxKshell >= kshell.size())
    MaxKshell=kshell.size()-1;
  
  Fk_symm.resize(MaxKshell);
  kMag.resize(MaxKshell);
  mRealType kgauss=1.0/(4*Sigma*Sigma);
  mRealType knorm=4*M_PI/Volume;
  const mRealType acclog=std::abs(std::log(1.0e-10));
  for(int ks=0,ki=0; ks<Fk_symm.size(); ks++)
  {
    mRealType t2e=KList.ksq[ki]*kgauss;
    mRealType uk=knorm*std::exp(-t2e)/KList.ksq[ki];
    Fk_symm[ks]=uk;
    while(ki<KList.kshell[ks+1] && ki<Fk.size())
      Fk[ki++]=Fkg[ki]=uk;
  }
  PreFactors[3]=0.0;
  app_log().flush();
}
}
