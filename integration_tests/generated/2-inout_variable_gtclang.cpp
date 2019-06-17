// gtclang (0.0.1-9b6d23a-x86_64-linux-gnu-5.4.0)
// based on LLVM/Clang (6.0.1), Dawn (0.0.1)
// Generated on 2019-06-17  12:12:43

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

namespace gridtools {

class test {
 public:
  struct stencil_12 {
    // Intervals
    using interval_start__end_ = gridtools::interval<gridtools::level<0, 1, 4>, gridtools::level<1, -1, 4>>;
    using axis_stencil_12 = gridtools::interval<gridtools::level<0, -1, 4>, gridtools::level<1, 1, 4>>;
    using grid_stencil_12 = gridtools::grid<axis_stencil_12>;

    struct stage_0_0 {
      using a = gridtools::accessor<0, gridtools::enumtype::inout, gridtools::extent<0, 0, 0, 0, 0, 0>>;
      using arg_list = boost::mpl::vector<a>;

      template <typename Evaluation>
      GT_FUNCTION static void Do(Evaluation& eval, interval_start__end_) {
        eval(a(0, 0, 0)) = (eval(a(0, 0, 0)) + (int)7);
      }
    };

    stencil_12(const gridtools::clang::domain& dom, storage_ijk_t a) {
      // Check if extents do not exceed the halos
      using p_a = gridtools::arg<0, storage_ijk_t>;
      using domain_arg_list = boost::mpl::vector<p_a>;

      // Grid
      gridtools::halo_descriptor di = {dom.iminus(), dom.iminus(), dom.iplus(), dom.isize() - 1 - dom.iplus(),
                                       dom.isize()};
      gridtools::halo_descriptor dj = {dom.jminus(), dom.jminus(), dom.jplus(), dom.jsize() - 1 - dom.jplus(),
                                       dom.jsize()};
      auto grid_ = grid_stencil_12(di, dj);
      grid_.value_list[0] = dom.kminus();
      grid_.value_list[1] = dom.ksize() == 0 ? 0 : dom.ksize() - dom.kplus();
      a.sync();

      // Computation
      m_stencil = gridtools::make_computation<backend_t>(
          grid_, (p_a() = a),
          gridtools::make_multistage(
              gridtools::enumtype::execute<gridtools::enumtype::forward /*parallel*/>(),
              gridtools::define_caches(
                  gridtools::cache<gridtools::K, gridtools::cache_io_policy::fill_and_flush>(p_a())),
              gridtools::make_stage_with_extent<stage_0_0, extent<0, 0, 0, 0>>(p_a())));
    }

    // Members
    computation<void> m_stencil;

    computation<void>* get_stencil() { return &m_stencil; }
  };

  // Stencil-Data
  const gridtools::clang::domain& m_dom;
  static constexpr const char* s_name = "test";

  // Members representing all the stencils that are called
  stencil_12 m_stencil_12;

 public:
  test(const test&) = delete;

  test(const gridtools::clang::domain& dom, storage_ijk_t a) : m_dom(dom), m_stencil_12(dom, a) {}

  void run() { m_stencil_12.get_stencil()->run(); }

  std::string get_name() const { return std::string(s_name); }

  std::vector<computation<void>*> getStencils() {
    return std::vector<gridtools::computation<void>*>({m_stencil_12.get_stencil()});
  }

  void reset_meters() { m_stencil_12.get_stencil()->reset_meter(); }
};
}  // namespace gridtools
