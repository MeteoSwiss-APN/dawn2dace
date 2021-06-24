// gtclang (0.0.1-0e3008e-x86_64-linux-gnu-7.4.0)
// based on LLVM/Clang (6.0.0), Dawn (0.0.1)
// Generated on 2019-10-25  15:38:49

#define GRIDTOOLS_CLANG_GENERATED 1
#define GRIDTOOLS_CLANG_BACKEND_T GT
#ifndef BOOST_RESULT_OF_USE_TR1
 #define BOOST_RESULT_OF_USE_TR1 1
#endif
#ifndef BOOST_NO_CXX11_DECLTYPE
 #define BOOST_NO_CXX11_DECLTYPE 1
#endif
#ifndef GRIDTOOLS_CLANG_HALO_EXTEND
 #define GRIDTOOLS_CLANG_HALO_EXTEND 3
#endif
#ifndef BOOST_PP_VARIADICS
 #define BOOST_PP_VARIADICS 1
#endif
#ifndef BOOST_FUSION_DONT_USE_PREPROCESSED_FILES
 #define BOOST_FUSION_DONT_USE_PREPROCESSED_FILES 1
#endif
#ifndef BOOST_MPL_CFG_NO_PREPROCESSED_HEADERS
 #define BOOST_MPL_CFG_NO_PREPROCESSED_HEADERS 1
#endif
#ifndef GT_VECTOR_LIMIT_SIZE
 #define GT_VECTOR_LIMIT_SIZE 40
#endif
#ifndef BOOST_FUSION_INVOKE_MAX_ARITY
 #define BOOST_FUSION_INVOKE_MAX_ARITY GT_VECTOR_LIMIT_SIZE
#endif
#ifndef FUSION_MAX_VECTOR_SIZE
 #define FUSION_MAX_VECTOR_SIZE GT_VECTOR_LIMIT_SIZE
#endif
#ifndef FUSION_MAX_MAP_SIZE
 #define FUSION_MAX_MAP_SIZE GT_VECTOR_LIMIT_SIZE
#endif
#ifndef BOOST_MPL_LIMIT_VECTOR_SIZE
 #define BOOST_MPL_LIMIT_VECTOR_SIZE GT_VECTOR_LIMIT_SIZE
#endif
#include "gridtools/clang_dsl.hpp"

using namespace gridtools::clang;

namespace dawn_generated {
namespace gt {

class test {
 public:
  using p_a = gridtools::arg<0, storage_ijk_t>;

  struct stencil_12 {
    // Intervals
    using interval_start__end_ = gridtools::interval<gridtools::level<0, 1, 3>, gridtools::level<1, -1, 3>>;
    using axis_stencil_12 = gridtools::interval<gridtools::level<0, -1, 3>, gridtools::level<1, 1, 3>>;
    using grid_stencil_12 = gridtools::grid<axis_stencil_12>;

    struct stage_0_0 {
      using a = gridtools::accessor<0, gridtools::intent::inout, gridtools::extent<0, 0, 0, 0, 0, 0>>;
      using param_list = gridtools::make_param_list<a>;

      template <typename Evaluation>
      GT_FUNCTION static void apply(Evaluation& eval, interval_start__end_) {
        eval(a(0, 0, 0)) = (eval(a(0, 0, 0)) + (int)7);
      }
    };

    stencil_12(const gridtools::clang::domain& dom) {
      // Check if extents do not exceed the halos

      // Grid
      gridtools::halo_descriptor di = {dom.iminus(), dom.iminus(), dom.iplus(), dom.isize() - 1 - dom.iplus(),
                                       dom.isize()};
      gridtools::halo_descriptor dj = {dom.jminus(), dom.jminus(), dom.jplus(), dom.jsize() - 1 - dom.jplus(),
                                       dom.jsize()};
      grid_stencil_12 grid_(di, dj, {dom.kminus(), dom.ksize() == 0 ? 0 : dom.ksize() - dom.kplus()});

      // Computation
      m_stencil = gridtools::make_computation<backend_t>(
          grid_, gridtools::make_multistage(
                     gridtools::execute::forward /*parallel*/ (),
                     gridtools::make_stage_with_extent<stage_0_0, gridtools::extent<0, 0, 0, 0>>(p_a())));
    }

    // Members
    gridtools::computation<p_a> m_stencil;

    gridtools::computation<p_a>* get_stencil() { return &m_stencil; }
  };

  // Stencil-Data
  const gridtools::clang::domain& m_dom;
  static constexpr const char* s_name = "test";

  // Members representing all the stencils that are called
  stencil_12 m_stencil_12;

 public:
  test(const test&) = delete;

  test(const gridtools::clang::domain& dom, storage_ijk_t /*unused*/) : m_dom(dom), m_stencil_12(dom) {}

  template <typename S>
  void sync_storages(S field) {
    field.sync();
  }

  template <typename S0, typename... S>
  void sync_storages(S0 f0, S... fields) {
    f0.sync();
    sync_storages(fields...);
  }

  void run(storage_ijk_t a) {
    sync_storages(a);
    m_stencil_12.get_stencil()->run(p_a{} = a);
    sync_storages(a);
  }

  std::string get_name() const { return std::string(s_name); }

  void reset_meters() { m_stencil_12.get_stencil()->reset_meter(); }

  double get_total_time() {
    double res = 0;
    res += m_stencil_12.get_stencil()->get_time();
    return res;
  }
};
}  // namespace gt
}  // namespace dawn_generated
