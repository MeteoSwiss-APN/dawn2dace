#define GRIDTOOLS_CLANG_HALO_EXTEND 3
#define GRIDTOOLS_CLANG_GENERATED 1

#include "generated/2-inout_variable_dace.cpp"
#include "generated/2-inout_variable_gtclang.cpp"
#include "gridtools/clang/verify.hpp"
#include <cassert>

int main(int argc, char const *argv[]) {

  // Read the domain Size
  int x = atoi(argv[1]);
  int y = atoi(argv[2]);
  int z = atoi(argv[3]);

  // Setup of the gridtools strorages and the verfier
  domain dom(x, y, z);
  dom.set_halos(halo::value, halo::value, halo::value, halo::value, 0, 0);
  meta_data_t meta_data(dom.isize(), dom.jsize(), dom.ksize() + 1);
  verifier verif(dom);

  // Input fields
  storage_t input_gtclang(meta_data, "input");
  storage_t input_dace(meta_data, "input");

  verif.fillMath(8.0, 2.0, 1.5, 1.5, 2.0, 4.0, input_gtclang, input_dace);

  // Call the gtclang stencil
  dawn_generated::gt::test test_gtclang(dom, input_gtclang);
  test_gtclang.run();

  // call the dapp-stencil
  auto raw_input_dace = gridtools::make_host_view(input_dace).data();

  __program_IIRToSDFG(raw_input_dace, x, y, z, halo::value);

  assert(verif.verify(input_gtclang, input_dace));

  std::cout << "verification successful" << std::endl;
  return 0;
}
