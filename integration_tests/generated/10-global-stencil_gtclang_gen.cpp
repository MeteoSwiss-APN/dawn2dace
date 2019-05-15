// gtclang (0.0.1-42ba1b2-x86_64-linux-gnu-5.4.0)
// based on LLVM/Clang (6.0.1), Dawn (0.0.1)
// Generated on 2019-05-15  14:16:33

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

struct globals {
  double global2;
  double testglobal;

  globals() {}
};
}  // namespace gridtools

namespace gridtools {

class test {
 public:
  struct stencil_15 {
    const globals& m_globals;
    decltype(backend_t::make_global_parameter(m_globals)) m_globals_gp_;

    // Intervals
    using interval_start__end_ = gridtools::interval<gridtools::level<0, 1, 4>, gridtools::level<1, -1, 4>>;
    using axis_stencil_15 = gridtools::interval<gridtools::level<0, -1, 4>, gridtools::level<1, 1, 4>>;
    using grid_stencil_15 = gridtools::grid<axis_stencil_15>;

    struct stage_0_0 {
      using in_field = gridtools::accessor<0, gridtools::enumtype::in, gridtools::extent<0, 0, 0, 0, 0, 0>>;
      using out_field = gridtools::accessor<1, gridtools::enumtype::inout, gridtools::extent<0, 0, 0, 0, 0, 0>>;
      using globals = gridtools::global_accessor<2>;
      using arg_list = boost::mpl::vector<in_field, out_field, globals>;

      template <typename Evaluation>
      GT_FUNCTION static void Do(Evaluation& eval, interval_start__end_) {
        eval(out_field(0, 0, 0)) = ((eval(in_field(0, 0, 0)) + eval(globals()).testglobal) + eval(globals()).global2);
      }
    };

    stencil_15(const gridtools::clang::domain& dom, const globals& globals, storage_ijk_t in_field,
               storage_ijk_t out_field)
        : m_globals(globals), m_globals_gp_(backend_t::make_global_parameter(m_globals)) {
      // Check if extents do not exceed the halos
      static_assert((static_cast<int>(storage_ijk_t::storage_info_t::halo_t::template at<0>()) >= 0) ||
                        (storage_ijk_t::storage_info_t::layout_t::template at<0>() == -1),
                    "Used extents exceed halo limits.");
      static_assert(((-1) * static_cast<int>(storage_ijk_t::storage_info_t::halo_t::template at<0>()) <= 0) ||
                        (storage_ijk_t::storage_info_t::layout_t::template at<0>() == -1),
                    "Used extents exceed halo limits.");
      static_assert((static_cast<int>(storage_ijk_t::storage_info_t::halo_t::template at<1>()) >= 0) ||
                        (storage_ijk_t::storage_info_t::layout_t::template at<1>() == -1),
                    "Used extents exceed halo limits.");
      static_assert(((-1) * static_cast<int>(storage_ijk_t::storage_info_t::halo_t::template at<1>()) <= 0) ||
                        (storage_ijk_t::storage_info_t::layout_t::template at<1>() == -1),
                    "Used extents exceed halo limits.");
      static_assert((static_cast<int>(storage_ijk_t::storage_info_t::halo_t::template at<0>()) >= 0) ||
                        (storage_ijk_t::storage_info_t::layout_t::template at<0>() == -1),
                    "Used extents exceed halo limits.");
      static_assert(((-1) * static_cast<int>(storage_ijk_t::storage_info_t::halo_t::template at<0>()) <= 0) ||
                        (storage_ijk_t::storage_info_t::layout_t::template at<0>() == -1),
                    "Used extents exceed halo limits.");
      static_assert((static_cast<int>(storage_ijk_t::storage_info_t::halo_t::template at<1>()) >= 0) ||
                        (storage_ijk_t::storage_info_t::layout_t::template at<1>() == -1),
                    "Used extents exceed halo limits.");
      static_assert(((-1) * static_cast<int>(storage_ijk_t::storage_info_t::halo_t::template at<1>()) <= 0) ||
                        (storage_ijk_t::storage_info_t::layout_t::template at<1>() == -1),
                    "Used extents exceed halo limits.");
      using p_in_field = gridtools::arg<0, storage_ijk_t>;
      using p_out_field = gridtools::arg<1, storage_ijk_t>;
      using p_globals = gridtools::arg<2, decltype(m_globals_gp_)>;
      using domain_arg_list = boost::mpl::vector<p_in_field, p_out_field, p_globals>;

      // Grid
      gridtools::halo_descriptor di = {dom.iminus(), dom.iminus(), dom.iplus(), dom.isize() - 1 - dom.iplus(),
                                       dom.isize()};
      gridtools::halo_descriptor dj = {dom.jminus(), dom.jminus(), dom.jplus(), dom.jsize() - 1 - dom.jplus(),
                                       dom.jsize()};
      auto grid_ = grid_stencil_15(di, dj);
      grid_.value_list[0] = dom.kminus();
      grid_.value_list[1] = dom.ksize() == 0 ? 0 : dom.ksize() - dom.kplus();
      in_field.sync();
      out_field.sync();

      // Computation
      m_stencil = gridtools::make_computation<backend_t>(
          grid_, (p_in_field() = in_field), (p_out_field() = out_field), (p_globals() = m_globals_gp_),
          gridtools::make_multistage(gridtools::enumtype::execute<gridtools::enumtype::forward /*parallel*/>(),
                                     gridtools::make_stage_with_extent<stage_0_0, extent<0, 0, 0, 0>>(
                                         p_in_field(), p_out_field(), p_globals())));
    }

    // Members
    computation<void> m_stencil;

    void update_globals() { backend_t::update_global_parameter(m_globals_gp_, m_globals); }

    computation<void>* get_stencil() { return &m_stencil; }
  };

  // Stencil-Data
  const gridtools::clang::domain& m_dom;
  static constexpr const char* s_name = "test";
  globals m_globals;

  // Members representing all the stencils that are called
  stencil_15 m_stencil_15;

 public:
  test(const test&) = delete;

  test(const gridtools::clang::domain& dom, storage_ijk_t in_field, storage_ijk_t out_field)
      : m_dom(dom), m_stencil_15(dom, m_globals, in_field, out_field) {}

  void run() { m_stencil_15.get_stencil()->run(); }

  // Globals API

  double get_testglobal() { return m_globals.testglobal; }

  void set_testglobal(double testglobal) {
    m_globals.testglobal = testglobal;
    m_stencil_15.update_globals();
  }

  double get_global2() { return m_globals.global2; }

  void set_global2(double global2) {
    m_globals.global2 = global2;
    m_stencil_15.update_globals();
  }

  std::string get_name() const { return std::string(s_name); }

  std::vector<computation<void>*> getStencils() {
    return std::vector<gridtools::computation<void>*>({m_stencil_15.get_stencil()});
  }

  void reset_meters() { m_stencil_15.get_stencil()->reset_meter(); }
};
}  // namespace gridtools
