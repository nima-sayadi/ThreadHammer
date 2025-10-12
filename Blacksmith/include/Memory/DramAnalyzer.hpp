/*
 * Copyright (c) 2021 by ETH Zurich.
 * Licensed under the MIT License, see LICENSE file for more details.
 */

#ifndef DRAMANALYZER
#define DRAMANALYZER

#include <cinttypes>
#include <vector>
#include <random>
#include <map> // Added for bank_to_channel
#ifdef ENABLE_JSON
#include <nlohmann/json.hpp>
#endif

#include "Utilities/AsmPrimitives.hpp"

class DramAnalyzer {
 private:
  std::vector<std::vector<volatile char *>> banks;

  // New: Separate vector for hugepage addresses per bank
  std::vector<std::vector<volatile char *>> random_bank_to_addresses_vec;

  std::vector<uint64_t> bank_rank_functions;

  uint64_t row_function;

  volatile char *start_address;

  void find_targets(std::vector<volatile char *> &target_bank);

  std::mt19937 gen;

  std::uniform_int_distribution<int> dist;

  // New: Mapping from bank to channel related variables
  std::map<size_t, size_t> bank_to_channel;
  std::map<size_t, uint64_t> bank_timing_data;


 public:
  explicit DramAnalyzer(volatile char *target);

  /// Finds addresses of the same bank causing bank conflicts when accessed sequentially
  void find_bank_conflicts();

  /// Measures the time between accessing two addresses.
  static int inline measure_time(volatile char *a1, volatile char *a2) {
    uint64_t before, after;
    before = rdtscp();
    lfence();
    for (size_t i = 0; i < DRAMA_ROUNDS; i++) {
      (void)*a1;
      (void)*a2;
      clflushopt(a1);
      clflushopt(a2);
      mfence();
    }
    after = rdtscp();
    return (int) ((after - before)/DRAMA_ROUNDS);
  }

  std::vector<uint64_t> get_bank_rank_functions();

  void load_known_functions(int num_ranks);

  /// Determine the number of possible activations within a refresh interval.
  size_t count_acts_per_trefi();

  // New: Measure and assign channels to banks
  void measure_and_assign_channels(uint64_t nMeasurements = 50);

  // New: Initialize banks with addresses from hugepage
  void create_addresses(size_t addresses_per_bank = 1000);

  // New: Getter for random_bank_to_addresses_vec
  const std::vector<std::vector<volatile char *>>& get_random_bank_to_addresses_vec() const { return random_bank_to_addresses_vec; }
  
  // New: Json for channel assignment
  #ifdef ENABLE_JSON
    nlohmann::json get_bank_to_channel_json() const;
  #endif
};

#endif /* DRAMANALYZER */
