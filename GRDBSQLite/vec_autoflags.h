#pragma once

#if (defined(__x86_64__) || defined(_M_X64)) && !defined(SQLITE_VEC_ENABLE_AVX)
#  define SQLITE_VEC_ENABLE_AVX 1
#endif

#if (defined(__ARM_NEON) || defined(__ARM_NEON__)) && !defined(SQLITE_VEC_ENABLE_NEON)
#  define SQLITE_VEC_ENABLE_NEON 1
#endif
