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
#ifndef GRIDTOOLS_CLANG_BENCHMARK_WRITER_HPP
#define GRIDTOOLS_CLANG_BENCHMARK_WRITER_HPP

#include <unordered_map>
#include <vector>

namespace gridtools {

namespace clang {

class benchmarker {

public:
  benchmarker(int nIter);

  ///@brief runs the benchmaks of the given computation and wirtes the output to the specified .json
  /// file
  template <typename GTStencil>
  void runBenchmarks(GTStencil& computation) {

    // Run an inital run to not get polluted data
    computation.run();

    // Gather the data from the actual runs
    stencilName_ = computation.get_name();
    for(int i = 0; i < nIter_; ++i) {
      computation.reset_meters();
      computation.run();
      auto stencils = computation.getStencils();
      for(auto stencil : stencils) {
        times_[i] += stencil->get_time();
      }
    }
  }
  ///@brief write the output to the specified json file
  void writeToJson(std::string filename);

  ///@brief write the output to std::cout with the [ output ] prefix
  void writeToStdOut();

  ///@brief intiializes the .json file with the required meta-information that is passed in the
  /// configuartion-vector and the domain size. The configuartion vector contaions:
  void initOutput(std::unordered_map<std::string, std::string>& optionToArgumentMap,
                  const std::vector<int>& domainsize, std::string filename) const;

private:
  int nIter_;
  std::vector<double> times_;
  std::string stencilName_;
};
}
}

#endif // GRIDTOOLS_CLANG_BENCHMARK_WRITER_HPP
