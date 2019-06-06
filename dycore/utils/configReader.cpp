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
#include <string>
#include <unordered_map>
#include <iostream>
#include <cstring>
#include <algorithm>
#include <sstream>
#include <iterator>

using namespace gridtools::clang;

///@brief Value type used for storing command line arguments [as strings] by the ArgumentParser
class Value {
public:
  Value(std::string content) : content_(content) {}
  Value() : Value("") {}

  double returnDouble(double d = 0) const {
    if(content_ == "")
      return d;
    return (double)std::atof(content_.c_str());
  }
  std::string returnString(std::string d = "") const {
    if(content_ == "")
      return d;
    return content_;
  }

private:
  std::string content_;
};

///@brief simple argument parser for doubles and strings
class ArgumentParser {
public:
  Value operator()(const std::string arg) { return mapArguments_[arg]; }
  Value operator()(const std::string arg, bool required) {
    if(required && mapArguments_.count(arg) == 0) {
      std::cerr << "required argument " << arg << " not provided" << std::endl;
      throw;
    }
    return mapArguments_[arg];
  }

  ArgumentParser(const int argc, const char** argv) : mapArguments_(), argc_(argc), argv_(argv) {
    for(int i = 1; i < argc; i++) {
      if(argv[i][0] == '-') {
        std::string values = "";
        int itemCount = 0;

        for(int j = i + 1; j < argc; j++) {
          if(argv[j][0] == '-') {
            break;
          } else {
            if(strcmp(values.c_str(), "")) {
              values += ' ';
            }

            values += argv[j];
            itemCount++;
          }
        }
        if(itemCount == 0) {
          values += "default";
        }
        mapArguments_[argv[i]] = Value(values);
        i += itemCount;
      }
    }
  }

private:
  std::unordered_map<std::string, Value> mapArguments_;
  const int argc_;
  const char** argv_;
};

///@brief the configuartion Reader initializes the .json file for benchmarking with the
/// metainformation required by the pyutils library we use to plot benchmarking numbers
int main(int argc, const char** argv) {
  ArgumentParser parser(argc, argv);
  // Required Arugments to write a useful file
  std::string machine = parser("-machine", true).returnString();
  std::string backend = parser("-backend", true).returnString();
  std::string compiler = parser("-compiler", true).returnString();

  // parse the metadata given as input
  std::unordered_map<std::string, std::string> optionToArgumentMap;
  optionToArgumentMap.emplace("clustername", machine);
  optionToArgumentMap.emplace("configurationname", parser("-config").returnString(machine));
  optionToArgumentMap.emplace("hostname", parser("-hostname").returnString(machine));
  optionToArgumentMap.emplace("backend", backend);
  optionToArgumentMap.emplace("compiler", compiler);
  optionToArgumentMap.emplace("gridtype", parser("-gridtype").returnString("structured"));
  optionToArgumentMap.emplace("runname",
                              parser("-name").returnString("cosmo-prerelease-gtclang-dycore"));
  optionToArgumentMap.emplace("precision", parser("precision").returnString("double"));
  optionToArgumentMap.emplace("gittag", parser("-gittag").returnString());
  optionToArgumentMap.emplace("version", std::to_string(parser("-version").returnDouble(0.4)));

  // parse the domain size
  std::string domainString = parser("-dim").returnString();
  std::istringstream buf(domainString);
  std::istream_iterator<std::string> beg(buf), end;
  std::vector<std::string> tokens(beg, end);
  std::vector<int> domainsize;
  std::transform(tokens.begin(), tokens.end(), std::back_inserter(domainsize),
                 [](const std::string& str) { return std::stoi(str); });

  // find the filename to write the metadata
  std::string filename = parser("-filename").returnString("test.json");

  // initialize the json file
  benchmarker bench(0);
  bench.initOutput(optionToArgumentMap, domainsize, filename);
  return 0;
}
