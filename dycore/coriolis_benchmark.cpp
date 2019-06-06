//===--------------------------------------------------------------------------------*- C++ -*-===//
//
//                      _       _                         _
//                     | |     | |                       | |
//                 __ _| |_ ___| | __ _ _ __   __ _    __| |_   _  ___ ___  _ __ ___
//                / _` | __/ __| |/ _` | '_ \ / _` |  / _` | | | |/ __/ _ \| '__/ _ \
//               | (_| | || (__| | (_| | | | | (_| | | (_| | |_| | (_| (_) | | |  __/
//                \__, |\__\___|_|\__,_|_| |_|\__, |  \__,_|\__, |\___\___/|_|  \___|
//                 __/ |                       __/ |         __/ |
//                |___/                       |___/         |___/
//
//                       - applied exaples of the gtclang/dawn toolchain to the COSMO dynamical core
//
//  This file is distributed under the MIT License (MIT).
//  See LICENSE.txt for details.
//===------------------------------------------------------------------------------------------===//
#define GRIDTOOLS_CLANG_HALO_EXTEND 3
#define GRIDTOOLS_CLANG_GENERATED 1

#include "gen/coriolis_dace_gen.cpp"
#include "gen/coriolis_gtclang_gen.cpp"
#include "gridtools/clang/verify.hpp"
#include "utils/benchmark_writer.hpp"
#include <cassert>

int main(int argc, char const* argv[]) {

  // Read the domain Size
  int x = atoi(argv[1]);
  int y = atoi(argv[2]);
  int z = atoi(argv[3]);
  std::string benchFile = "";
  int niter = 0;
  if(argc > 4) {
    niter = atoi(argv[4]);
  }
  if(argc > 5) {
    benchFile = argv[5];
  }

  // Setup of the gridtools strorages and the verfier
  domain dom(x, y, z);
  dom.set_halos(halo::value, halo::value, halo::value, halo::value, 0, 0);
  meta_data_t meta_data(dom.isize(), dom.jsize(), dom.ksize());
  verifier verif(dom);

  // Output fields
  storage_t u_tens_gtclang(meta_data, "u_tens_gtclang");
  storage_t v_tens_gtclang(meta_data, "v_tens_gtclang");
  storage_t u_tens_dace(meta_data, "u_tens_dace");
  storage_t v_tens_dace(meta_data, "v_tens_dace");

  verif.fillMath(8.0, 2.0, 1.5, 1.5, 2.0, 4.0, u_tens_gtclang, u_tens_dace);
  verif.fillMath(2.0, 3.2, 1.1, 8.5, 2.0, 2.2, v_tens_gtclang, v_tens_dace);

  // Input fields
  storage_t u_nnow(meta_data, "u_nnow");
  storage_t v_nnow(meta_data, "v_nnow");
  storage_t fc(meta_data, "fc");

  verif.fillMath(6.0, 2.0, 1.5, 2.8, 2.0, 4.1, u_nnow);
  verif.fillMath(4.0, 1.7, 1.5, 6.3, 2.0, 1.4, v_nnow);
  verif.fillMath(8.0, 9.4, 1.5, 1.7, 2.0, 3.5, fc);

  // Call the gtclang stencil
  gridtools::coriolis_stencil coriolis_gtclang(dom, u_tens_gtclang, v_tens_gtclang, u_nnow, v_nnow,
                                               fc);
  coriolis_gtclang.run();

  // call the dapp-stencil
  auto raw_u_tens_dace = gridtools::make_host_view(u_tens_dace).data();
  auto raw_v_tens_dace = gridtools::make_host_view(v_tens_dace).data();
  auto raw_u_nnow = gridtools::make_host_view(u_nnow).data();
  auto raw_v_nnow = gridtools::make_host_view(v_nnow).data();
  auto raw_fc = gridtools::make_host_view(fc).data();

  __program_IIRToSDFG(raw_fc, raw_u_tens_dace, raw_v_nnow, raw_v_tens_dace, raw_u_nnow, x, y, z,
                      halo::value);

  assert(verif.verify(u_tens_gtclang, u_tens_dace));
  assert(verif.verify(v_tens_gtclang, v_tens_dace));

  std::cout << "verification successful" << std::endl;

  benchmarker bench(niter);
  bench.runBenchmarks(coriolis_gtclang);
  bench.writeToStdOut();
  if(benchFile != "") {
    bench.writeToJson(benchFile);
  }
  return 0;
}
