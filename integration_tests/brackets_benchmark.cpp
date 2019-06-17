#define GRIDTOOLS_CLANG_HALO_EXTEND 3
#define GRIDTOOLS_CLANG_GENERATED 1

#include "generated/8-brackets_dace.cpp"
#include "generated/8-brackets_gtclang.cpp"
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
  storage_t out_dapp(meta_data, "out_dapp");

  verif.fill(-1.0, out_gtclang, out_dapp);

  // Input fields
  storage_t input(meta_data, "input");

  verif.fillMath(8.0, 2.0, 1.5, 1.5, 2.0, 4.0, input);

  // Call the gtclang stencil
  gridtools::test test_gtclang(dom, input, out_gtclang);
  test_gtclang.run();

  // call the dapp-stencil
  auto raw_out_dapp = gridtools::make_host_view(out_dapp).data();
  auto raw_input = gridtools::make_host_view(input).data();

  __program_IIRToSDFG(raw_input, raw_out_dapp, x, y, z, halo::value);

  assert(verif.verify(out_gtclang, out_dapp));

  std::cout << "verification successful" << std::endl;
  return 0;
}
