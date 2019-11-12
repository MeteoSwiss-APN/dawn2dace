#include "gridtools/clang_dsl.hpp"

using namespace gridtools::clang;

globals
{
  double global_var = 3.14;
};

stencil scopes
{
  storage input, output;
  var stencil_var;
  
  Do
  {
    vertical_region(k_start, k_end)
    {
      double region_var = input;
      stencil_var = region_var;
      output = stencil_var[i-1] + global_var;
    }
  }
};

