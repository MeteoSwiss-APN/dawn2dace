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
#include "benchmark_writer.hpp"
#include "External/json/json.hpp"
#include <chrono>
#include <ctime>
#include <fstream>
#include <algorithm>
#include <sstream>

namespace gridtools {

namespace clang {

benchmarker::benchmarker(int nIter = 100) : nIter_(nIter), times_(nIter, 0) {}

void benchmarker::writeToJson(std::string filename) {
  using json = nlohmann::json;
  // Read the existing file
  std::ifstream fsin(filename);
  if(!fsin.is_open()) {
    std::cerr << "could not open file" << filename << std::endl;
    assert(false);
  }
  if(fsin.peek() == std::ifstream::traits_type::eof()) {
    std::cerr << "\nbenchmark-file was not initialized, call benchmarker.initOutput() for "
              << filename << "\n"
              << std::endl;
    assert(false);
  }
  json j;
  fsin >> j;
  fsin.close();

  // Emplace the new times
  json jMesurement(times_);
  json jData;
  jData["measurements"] = jMesurement;
  jData["stencil"] = stencilName_;
  json jArray = json::array();
  jArray.push_back(jData);
  j["times"].push_back(jData);

  std::ofstream fsout(filename, std::ios::out | std::ios::trunc);
  fsout << j.dump(2) << std::endl;
  fsout.close();
}

void benchmarker::writeToStdOut() {
  double average = std::accumulate(times_.begin(), times_.end(), 0.0) / times_.size();
  std::cout << "\033[0;33m[  output  ] \033[0;0m Stencil: " << stencilName_
            << "\n\033[0;33m[  output  ] \033[0;0m Average Time: " << average
            << "\n\033[0;33m[  output  ] \033[0;0m Number of Iterations: " << times_.size()
            << std::endl;
}

///@brief intiializes the .json file with the required meta-information that is passed in the
/// configuartion-vector and the domain size. The configuartion vector contaions:
void benchmarker::initOutput(std::unordered_map<std::string, std::string>& optionToArgumentMap,
                             const std::vector<int>& domainsize, std::string filename) const {
  using json = nlohmann::json;
  // get the current time as GMT string
  std::chrono::time_point<std::chrono::system_clock> time;
  time = std::chrono::system_clock::now();
  std::time_t current_time = std::chrono::system_clock::to_time_t(time);
  auto gmt_time = gmtime(&current_time);
  std::ostringstream oss;
  oss << std::put_time(gmt_time, "%Y-%m-%d %H:%M:%S");
  std::string timestring = oss.str();

  // Specific format required form GT: {Y}-{M}-{D}T{H}:{M}:{S}.00000+0000
  std::replace(timestring.begin(), timestring.end(), ' ', 'T');
  timestring.append(".00000+0000");

  json jOut;
  json jConfig;
  auto findOrAssert = [&](std::string key) {
    assert(optionToArgumentMap.find(key) != optionToArgumentMap.end());
    return optionToArgumentMap[key];
  };
  jConfig["clustername"] = findOrAssert("clustername");
  jConfig["configname"] = findOrAssert("configurationname");
  jConfig["hostname"] = findOrAssert("hostname");
  jOut["config"] = jConfig;
  jOut["datetime"] = timestring;

  json jDomain(domainsize);
  jOut["domain"] = jDomain;

  json jRuntime;
  jRuntime["backend"] = findOrAssert("backend");
  jRuntime["compiler"] = findOrAssert("compiler");
  jRuntime["datetime"] = timestring;
  jRuntime["grid"] = findOrAssert("gridtype");
  jRuntime["name"] = findOrAssert("runname");
  jRuntime["precision"] = findOrAssert("precision");
  jRuntime["version"] = findOrAssert("gittag");
  jOut["runtime"] = jRuntime;
  jOut["version"] = std::atof(findOrAssert("version").c_str());

  std::ofstream fs(filename, std::ios::out | std::ios::trunc);
  if(!fs.is_open()) {
    std::cerr << "could not open file" << filename << std::endl;
    assert(false);
  }

  fs << jOut.dump(2) << std::endl;
  fs.close();
}
}
}
