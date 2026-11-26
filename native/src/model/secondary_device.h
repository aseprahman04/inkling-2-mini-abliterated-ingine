#pragma once

#include "core/device.h"

namespace ingine::model {

// The two-device path enters from GPU 0. Restore the caller's device even if allocation or upload throws.
class OnSecondary {
 public:
  OnSecondary() {
    CUDA_CHECK(cudaGetDevice(&previous_));
    CUDA_CHECK(cudaSetDevice(1));
  }
  ~OnSecondary() { cudaSetDevice(previous_); }
  OnSecondary(const OnSecondary&) = delete;
  OnSecondary& operator=(const OnSecondary&) = delete;
 private:
  int previous_;
};
}  // namespace ingine::model
