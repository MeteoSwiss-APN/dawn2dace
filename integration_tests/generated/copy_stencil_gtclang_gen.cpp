// gtclang (0.0.1-a2ac2a9-x86_64-linux-gnu-5.4.0)
// based on LLVM/Clang (3.8.0), Dawn (0.0.1)
// Generated on 2019-02-18  16:46:56

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
#include "gridtools/clang_dsl.hpp"

using namespace gridtools::clang;

namespace gridtools {

class copy_stencil {
public:
  struct stencil_11 {
    // Intervals
    using interval_start__end_ =
        gridtools::interval<gridtools::level<0, 1, 4>, gridtools::level<1, -1, 4>>;
    using axis_stencil_11 =
        gridtools::interval<gridtools::level<0, -1, 4>, gridtools::level<1, 1, 4>>;
    using grid_stencil_11 = gridtools::grid<axis_stencil_11>;

    struct stage_0_0 {
      using data_in =
          gridtools::accessor<0, gridtools::enumtype::in, gridtools::extent<0, 0, 0, 0, 0, 0>>;
      using data_out =
          gridtools::accessor<1, gridtools::enumtype::inout, gridtools::extent<0, 0, 0, 0, 0, 0>>;
      using arg_list = boost::mpl::vector<data_in, data_out>;

      template <typename Evaluation>
      GT_FUNCTION static void Do(Evaluation& eval, interval_start__end_) {
        eval(data_out(0, 0, 0)) = eval(data_in(0, 0, 0));
      }
    };

    stencil_11(const gridtools::clang::domain& dom, storage_ijk_t data_in, storage_ijk_t data_out) {
      // Check if extents do not exceed the halos
      static_assert(
          (static_cast<int>(storage_ijk_t::storage_info_t::halo_t::template at<0>()) >= 0) ||
              (storage_ijk_t::storage_info_t::layout_t::template at<0>() == -1),
          "Used extents exceed halo limits.");
      static_assert(
          ((-1) * static_cast<int>(storage_ijk_t::storage_info_t::halo_t::template at<0>()) <= 0) ||
              (storage_ijk_t::storage_info_t::layout_t::template at<0>() == -1),
          "Used extents exceed halo limits.");
      static_assert(
          (static_cast<int>(storage_ijk_t::storage_info_t::halo_t::template at<1>()) >= 0) ||
              (storage_ijk_t::storage_info_t::layout_t::template at<1>() == -1),
          "Used extents exceed halo limits.");
      static_assert(
          ((-1) * static_cast<int>(storage_ijk_t::storage_info_t::halo_t::template at<1>()) <= 0) ||
              (storage_ijk_t::storage_info_t::layout_t::template at<1>() == -1),
          "Used extents exceed halo limits.");
      static_assert(
          (static_cast<int>(storage_ijk_t::storage_info_t::halo_t::template at<0>()) >= 0) ||
              (storage_ijk_t::storage_info_t::layout_t::template at<0>() == -1),
          "Used extents exceed halo limits.");
      static_assert(
          ((-1) * static_cast<int>(storage_ijk_t::storage_info_t::halo_t::template at<0>()) <= 0) ||
              (storage_ijk_t::storage_info_t::layout_t::template at<0>() == -1),
          "Used extents exceed halo limits.");
      static_assert(
          (static_cast<int>(storage_ijk_t::storage_info_t::halo_t::template at<1>()) >= 0) ||
              (storage_ijk_t::storage_info_t::layout_t::template at<1>() == -1),
          "Used extents exceed halo limits.");
      static_assert(
          ((-1) * static_cast<int>(storage_ijk_t::storage_info_t::halo_t::template at<1>()) <= 0) ||
              (storage_ijk_t::storage_info_t::layout_t::template at<1>() == -1),
          "Used extents exceed halo limits.");
      using p_data_in = gridtools::arg<0, storage_ijk_t>;
      using p_data_out = gridtools::arg<1, storage_ijk_t>;
      using domain_arg_list = boost::mpl::vector<p_data_in, p_data_out>;

      // Grid
      gridtools::halo_descriptor di = {dom.iminus(), dom.iminus(), dom.iplus(),
                                       dom.isize() - 1 - dom.iplus(), dom.isize()};
      gridtools::halo_descriptor dj = {dom.jminus(), dom.jminus(), dom.jplus(),
                                       dom.jsize() - 1 - dom.jplus(), dom.jsize()};
      auto grid_ = grid_stencil_11(di, dj);
      grid_.value_list[0] = dom.kminus();
      grid_.value_list[1] = dom.ksize() == 0 ? 0 : dom.ksize() - dom.kplus();
      data_in.sync();
      data_out.sync();

      // Computation
      m_stencil = gridtools::make_computation<backend_t>(
          grid_, (p_data_in() = data_in), (p_data_out() = data_out),
          gridtools::make_multistage(
              gridtools::enumtype::execute<gridtools::enumtype::forward /*parallel*/>(),
              gridtools::make_stage_with_extent<stage_0_0, extent<0, 0, 0, 0>>(p_data_in(),
                                                                               p_data_out())));
    }

    // Members
    computation<void> m_stencil;

    computation<void>* get_stencil() { return &m_stencil; }
  };

  // Stencil-Data
  const gridtools::clang::domain& m_dom;
  static constexpr const char* s_name = "copy_stencil";

  // Members representing all the stencils that are called
  stencil_11 m_stencil_11;

public:
  copy_stencil(const copy_stencil&) = delete;

  copy_stencil(const gridtools::clang::domain& dom, storage_ijk_t data_in, storage_ijk_t data_out)
      : m_dom(dom), m_stencil_11(dom, data_in, data_out) {}

  void run() { m_stencil_11.get_stencil()->run(); }

  std::string get_name() const { return std::string(s_name); }

  std::vector<computation<void>*> getStencils() {
    return std::vector<gridtools::computation<void>*>({m_stencil_11.get_stencil()});
  }

  void reset_meters() { m_stencil_11.get_stencil()->reset_meter(); }
};
} // namespace gridtools
