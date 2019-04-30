#define GRIDTOOLS_CLANG_HALO_EXTEND 3
#define GRIDTOOLS_CLANG_GENERATED 1

#include "generated/vertical-offsets_dace_gen.cpp"
#include "generated/vertical-offsets_gtclang_gen.cpp"
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
  meta_data_t meta_data(dom.isize(), dom.jsize(), dom.ksize());
  verifier verif(dom);

  // Output fields
  storage_t output_dace(meta_data, "output_dace");
  storage_t output_gtclang(meta_data, "output_gtclang");
  verif.fill(-1.0, output_dace, output_gtclang);

  // Input fields
  storage_t input_1(meta_data, "input_1");

  verif.fillMath(6.0, 2.0, 1.5, 2.8, 2.0, 4.1, input_1);

  // Call the gtclang stencil
  gridtools::test test_gtclang(dom, input_1, output_gtclang);
  test_gtclang.run();

  // call the dace-stencil
  auto raw_out_dace = gridtools::make_host_view(output_dace).data();
  auto raw_input_1 = gridtools::make_host_view(input_1).data();

  __program_IIRToSDFG(raw_input_1, raw_out_dace, x, y, z, halo::value);

  assert(verif.verify(output_dace, output_gtclang));

  std::cout << "verification successful" << std::endl;
  return 0;
}
