#include "Memory/DramAnalyzer.hpp"

#include <cassert>
#include <unordered_set>
#include <algorithm> // For std::min_element
#include <sched.h> // New: for channel assignment
#include "Memory/DRAMAddr.hpp" // For DRAMAddr class
#include "Utilities/Logger.hpp" // For Logger functions
#ifdef ENABLE_JSON
#include <nlohmann/json.hpp> // Channel Assignment reasons
#endif

void DramAnalyzer::find_bank_conflicts() {
  size_t nr_banks_cur = 0;
  int remaining_tries = NUM_BANKS*512;  // experimentally determined, may be unprecise | New: I have increased this from 256 to 512 to prevent early exit from Blacksmith.
  while (nr_banks_cur < NUM_BANKS && remaining_tries > 0) {
    reset:
    remaining_tries--;
    auto a1 = start_address + (dist(gen)%(MEM_SIZE/64))*64;
    auto a2 = start_address + (dist(gen)%(MEM_SIZE/64))*64;
    auto ret1 = measure_time(a1, a2);
    auto ret2 = measure_time(a1, a2);

    if ((ret1 > THRESH) && (ret2 > THRESH)) {
      bool all_banks_set = true;
      for (size_t i = 0; i < NUM_BANKS; i++) {
        if (banks.at(i).empty()) {
          all_banks_set = false;
        } else {
          auto bank = banks.at(i);
          ret1 = measure_time(a1, bank[0]);
          ret2 = measure_time(a2, bank[0]);
          if ((ret1 > THRESH) || (ret2 > THRESH)) {
            // possibly noise if only exactly one is true,
            // i.e., (ret1 > THRESH) or (ret2 > THRESH)
            goto reset;
          }
        }
      }

      // stop if we already determined addresses for each bank
      if (all_banks_set) return;

      // store addresses found for each bank
      assert(banks.at(nr_banks_cur).empty() && "Bank not empty");
      banks.at(nr_banks_cur).push_back(a1);
      banks.at(nr_banks_cur).push_back(a2);
      nr_banks_cur++;
    }
    if (remaining_tries==0) {
      Logger::log_error(format_string(
          "Could not find conflicting address sets. Is the number of banks (%d) defined correctly?",
          (int) NUM_BANKS));
      exit(1);
    }
  }

  Logger::log_info("Found bank conflicts.");
  for (auto &bank : banks) {
    find_targets(bank);
  }
  Logger::log_info("Populated addresses from different banks. Sanity Check Completed!"); // New: Modified to log better
}

void DramAnalyzer::find_targets(std::vector<volatile char *> &target_bank) {
  // create an unordered set of the addresses in the target bank for a quick lookup
  // std::unordered_set<volatile char*> tmp; tmp.insert(target_bank.begin(), target_bank.end());
  std::unordered_set<volatile char *> tmp(target_bank.begin(), target_bank.end());
  target_bank.clear();
  size_t num_repetitions = 5;

  while (tmp.size() < 10) {
    auto a1 = start_address + (dist(gen)%(MEM_SIZE/64))*64;
    if (tmp.count(a1) > 0) continue;
    uint64_t cumulative_times = 0;
    for (size_t i = 0; i < num_repetitions; i++) {
      for (const auto &addr : tmp) {
        cumulative_times += measure_time(a1, addr);
      }
    }
    cumulative_times /= num_repetitions;
    if ((cumulative_times/tmp.size()) > THRESH) {
      tmp.insert(a1);
      target_bank.push_back(a1);
    }
  }
}

// New: Find addresses for each bank from the allocated hugepage
// Stores Banks with their addresses in random_bank_to_addresses_vec
void DramAnalyzer::create_addresses(size_t addresses_per_bank) {
  Logger::log_info(format_string("Finding %zu addresses for each bank from the allocated hugepage...", addresses_per_bank));
  
  // Set the random_bank_to_addresses_vec vector
  random_bank_to_addresses_vec = std::vector<std::vector<volatile char *>>(NUM_BANKS);
  
    // For each bank, find addresses that belong to it
    for (size_t bank_id = 0; bank_id < NUM_BANKS; ++bank_id) {
        Logger::log_debug(format_string("Finding addresses for bank %zu...", bank_id));

        size_t found_addresses = 0;
        bool already_exists = false;

        // Use this logic to prevent infinite loop if it ever happens!
        // size_t attempts = 0;
        // const size_t max_attempts = addresses_per_bank * 100;
        // while (found_addresses < addresses_per_bank && attempts < max_attempts)

        while (found_addresses < addresses_per_bank) {
            // attempts++; Use this logic to prevent infinite loop if it ever happens!
            
            // Generate a random address within the hugepage
            auto random_addr = start_address + (dist(gen) % (MEM_SIZE / 64)) * 64;
            
            // Convert to DRAMAddr to get the bank
            DRAMAddr dram_addr((void *) random_addr);
            
            // Check if this address belongs to the target bank
            if (dram_addr.bank == bank_id) {
                // Verify it's not already in the bank's address list
                bool already_exists = false;
                for (const auto& existing_addr : random_bank_to_addresses_vec[bank_id]) {
                    if (existing_addr == random_addr) {
                    already_exists = true;
                    break;
                    }
                }
                
                if (!already_exists) {
                    random_bank_to_addresses_vec[bank_id].push_back(random_addr);
                    found_addresses++;
                    
                    if (found_addresses % 100 == 0) {
                    Logger::log_debug(format_string("Bank %zu: found %zu addresses.", bank_id, found_addresses));
                    }
                }
            }
        }
    Logger::log_info(format_string("Bank %zu: found %zu addresses successfully. Moving to the next bank...", bank_id, random_bank_to_addresses_vec[bank_id].size()));
    }
  
  Logger::log_info("Completed finding addresses for all banks from hugepage. Ready for channel detection...");
}

DramAnalyzer::DramAnalyzer(volatile char *target) :
  row_function(0), start_address(target) {
  std::random_device rd;
  gen = std::mt19937(rd());
  dist = std::uniform_int_distribution<>(0, std::numeric_limits<int>::max());
  banks = std::vector<std::vector<volatile char *>>(NUM_BANKS, std::vector<volatile char *>());
}

std::vector<uint64_t> DramAnalyzer::get_bank_rank_functions() {
  return bank_rank_functions;
}

void DramAnalyzer::load_known_functions(int num_ranks) {
  if (num_ranks==1) {
    bank_rank_functions = std::vector<uint64_t>({0x4080 , 0x1b300 , 0x48000 , 0x90000 , 0x120000});
    row_function = 0x3ffc0000;
  } else if (num_ranks==2) {
    bank_rank_functions = std::vector<uint64_t>({0x2040, 0x44000, 0x88000, 0x110000, 0x220000});
    row_function = 0x3ffc0000;
  } else {
    Logger::log_error("Cannot load bank/rank and row function if num_ranks is not 1 or 2.");
    exit(1);
  }

  Logger::log_info("Loaded bank/rank and row function:");
  Logger::log_data(format_string("Row function 0x%" PRIx64, row_function));
  std::stringstream ss;
  ss << "Bank/rank functions (" << bank_rank_functions.size() << "): ";
  for (auto bank_rank_function : bank_rank_functions) {
    ss << "0x" << std::hex << bank_rank_function << " ";
  }
  Logger::log_data(ss.str());
}

size_t DramAnalyzer::count_acts_per_trefi() {
  size_t skip_first_N = 50;
  // pick two random same-bank addresses
  volatile char *a = banks.at(0).at(0);
  volatile char *b = banks.at(0).at(1);

  std::vector<uint64_t> acts;
  uint64_t running_sum = 0;
  uint64_t before;
  uint64_t after;
  uint64_t count = 0;
  uint64_t count_old = 0;

  // computes the standard deviation
  auto compute_std = [](std::vector<uint64_t> &values, uint64_t running_sum, size_t num_numbers) {
    double mean = static_cast<double>(running_sum)/static_cast<double>(num_numbers);
    double var = 0;
    for (const auto &num : values) {
      if (static_cast<double>(num) < mean) continue;
      var += std::pow(static_cast<double>(num) - mean, 2);
    }
    auto val = std::sqrt(var/static_cast<double>(num_numbers));
    return val;
  };

  for (size_t i = 0;; i++) {
    // flush a and b from caches
    clflushopt(a);
    clflushopt(b);
    mfence();

    // get start timestamp and wait until we retrieved it
    before = rdtscp();
    lfence();

    // do DRAM accesses
    (void)*a;
    (void)*b;

    // get end timestamp
    after = rdtscp();

    count++;
    if ((after - before) > 1000) {
      if (i > skip_first_N && count_old!=0) {
        // multiply by 2 to account for both accesses we do (a, b)
        uint64_t value = (count - count_old)*2;
        acts.push_back(value);
        running_sum += value;
        // check after each 200 data points if our standard deviation reached 1 -> then stop collecting measurements
        if ((acts.size()%200)==0 && compute_std(acts, running_sum, acts.size())<3.0) break;
      }
      count_old = count;
    }
  }

  auto activations = (running_sum/acts.size());
  Logger::log_info("Determined the number of possible ACTs per refresh interval.");
  Logger::log_data(format_string("num_acts_per_tREFI: %lu", activations));

  return activations;
}

// New: Channel Assignment
void DramAnalyzer::measure_and_assign_channels(uint64_t nMeasurements) {

    create_addresses();
    Logger::log_info("Measuring... This will take a while. Please be patient!");
    using u64 = uint64_t;

    auto median_of = [](std::vector<u64>& v) -> u64 {
        if (v.empty()) return 0;
        std::sort(v.begin(), v.end());
        size_t n = v.size();
        return (n & 1) ? v[n/2] : (v[n/2 - 1] + v[n/2]) / 2;
    };

    if (CHANNEL != 2) {
        Logger::log_info("Channel Number is not 2! Exiting Threadhammer...");
        exit(EXIT_FAILURE);
    }

    bank_timing_data[0] = 0; // reference

    // Tunables
    const int REPS  = 20;    // repetitions per (a1,a2) pair

    std::vector<u64> pair_medians;
    std::vector<u64> rep_samples;
    rep_samples.reserve(REPS);

    for (size_t i = 1; i < NUM_BANKS; ++i) {

        pair_medians.clear();

        const size_t n0 = random_bank_to_addresses_vec[0].size();
        const size_t nI = random_bank_to_addresses_vec[i].size();

        for (size_t j = 0; j < n0; ++j) {
            volatile char* a1 = random_bank_to_addresses_vec[0][j];

            for (size_t k = 0; k < nI; ++k) {
                volatile char* a2 = random_bank_to_addresses_vec[i][k];

                rep_samples.clear();

                for (int rep = 0; rep < REPS; ++rep) {
                    sched_yield();
                    sched_yield();
                    sched_yield();
                    sched_yield();
                    sched_yield();
                    sched_yield();
                    sched_yield();
                    sched_yield();
                    sched_yield();
                    sched_yield();
                    u64 start = rdtscp();

                    for (int m = 0; m < nMeasurements; ++m) {
                        (void)*a1;
                        (void)*a2;
                        clflush(a1);
                        clflush(a2);
                        lfence();
                    }

                    u64 end = rdtscp();

                    rep_samples.push_back((end - start) / (u64)nMeasurements);
                }

                // median for this (a1,a2) pair
                pair_medians.push_back(median_of(rep_samples));
            }
        }

        // median across all pairs -> robust per-bank score
        bank_timing_data[i] = median_of(pair_medians);
    }

    // Threshold: median of non-zero per-bank scores
    std::vector<u64> nonzero;
    nonzero.reserve(NUM_BANKS);
    for (const auto& kv : bank_timing_data) if (kv.second > 0) nonzero.push_back(kv.second);
    u64 threshold = median_of(nonzero);

    // Assign channels
    for (size_t i = 0; i < NUM_BANKS; ++i) {
        bank_to_channel[i] = (random_bank_to_addresses_vec[i].empty()) ? 0 : (bank_timing_data[i] > threshold ? 1 : 0);
    }

    Logger::log_info("Assigned channels using median of medians over all address pairs.");
    Logger::log_data(format_string("%lu", threshold));
}

#ifdef ENABLE_JSON
nlohmann::json DramAnalyzer::get_bank_to_channel_json() const {
  nlohmann::json j;
  for (const auto& kv : bank_to_channel) {
    nlohmann::json bank_info;
    bank_info["channel"] = kv.second;
    bank_info["avg_timing"] = bank_timing_data.at(kv.first);
    j[std::to_string(kv.first)] = bank_info;
  }
  return j;
}
#endif