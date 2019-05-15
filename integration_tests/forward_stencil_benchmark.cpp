#define GRIDTOOLS_CLANG_HALO_EXTEND 3
#define GRIDTOOLS_CLANG_GENERATED 1

#include "generated/9-forward_stencil_dace_gen.cpp"
#include "generated/9-forward_stencil_gtclang_gen.cpp"
#include "gridtools/clang/verify.hpp"
#include <cassert>

int main(int argc, char const* argv[]) {

  // Read the domain Size
  int x = atoi(argv[1]);
  int y = atoi(argv[2]);
  int z = atoi(argv[3]);

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
  gridtools::test stencil_gtclang(dom, input, out_gtclang, input);
  stencil_gtclang.run();

  // call the dace-stencil
  auto raw_out_dace = gridtools::make_host_view(out_dace).data();
  auto raw_input = gridtools::make_host_view(input).data();

  __program_IIRToSDFG(raw_input, raw_out_dace, x, y, z, halo::value);

  assert(verif.verify(out_gtclang, out_dace));

  std::cout << "verification successful" << std::endl;
  return 0;
}
