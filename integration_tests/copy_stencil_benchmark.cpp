#define GRIDTOOLS_CLANG_HALO_EXTEND 3
#define GRIDTOOLS_CLANG_GENERATED 1

#define BOOST_OPTIONAL_USE_OLD_DEFINITION_OF_NONE
#define BOOST_OPTIONAL_CONFIG_USE_OLD_IMPLEMENTATION_OF_OPTIONAL

#include "generated/1-copy_stencil_gtclang.cpp"
#include "gridtools/clang/verify.hpp"
#include <cassert>

#include <dace/dace.h>
DACE_EXPORTED void __program_IIRToSDFG(double * __restrict__ data_in_t, double * __restrict__ data_out_t, int I, int J, int K, int halo_size);
  
int main(int argc, char const* argv[]) {

  // Read the domain Size
  int x = atoi(argv[1]);
  int y = atoi(argv[2]);
  int z = atoi(argv[3]);
  int reps = atoi(argv[4]);

  // Setup of the gridtools strorages and the verfier
  domain dom(x, y, z);
  dom.set_halos(halo::value, halo::value, halo::value, halo::value, 0, 0);
  meta_data_t meta_data(dom.isize(), dom.jsize(), dom.ksize() + 1);
  verifier verif(dom);

  // Output fields
  storage_t out_gtclang(meta_data, "out_gtclang");
  storage_t out_dace(meta_data, "out_dace");

  verif.fill(-1.0, out_gtclang, out_dace);

  // Input fields
  storage_t input(meta_data, "input");

  verif.fillMath(8.0, 2.0, 1.5, 1.5, 2.0, 4.0, input);

  // Call the gtclang stencil
  gridtools::copy_stencil copy_gtclang(dom, input, out_gtclang);
  copy_gtclang.run();

  // call the dace-stencil
  auto raw_out_dace = gridtools::make_host_view(out_dace).data();
  auto raw_input = gridtools::make_host_view(input).data();

  for (int rep = 0; rep < reps; ++rep)
    __program_IIRToSDFG(raw_input, raw_out_dace, x, y, z, halo::value);

  assert(verif.verify(out_gtclang, out_dace));

  std::cout << "verification successful" << std::endl;
  return 0;
}
