#include "gtclang_dsl_defs/gtclang_dsl.hpp"

using namespace gtclang::dsl;

globals
{
  double global_var = 3.14;
};

stencil scopes_mixed
{
  storage input, output;
  var stencil_var;
  
  Do
  {
    vertical_region(k_start, k_end)
    {
      double region_var = input;
      stencil_var = region_var;
      output = stencil_var + global_var;
    }
  }
};

