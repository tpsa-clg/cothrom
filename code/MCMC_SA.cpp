#include <stdlib.h>
#include <iostream>
#include <fstream>
#include <sstream>
#include <string>
#include <valarray>
using std::valarray;
#include <chrono>
#include <set>
#include "Map.h"
#include "statfuncs.h"


int main(int argc, char *argv[])
{
  // custom name for area of consideration - first command line argument
  std::string map_name = argv[1];
  // directory for reading population & neighbour data and saving configs
  std::string data_dir = "data/" + map_name + "/";

  std::string line;
  // read populations - one integer (population) per line (electoral division)
  vector<int> populations(0);
  std::ifstream pop_file(data_dir + "Population.txt");
  while (getline(pop_file, line)) populations.push_back(stoi(line));
  pop_file.close();
  // read neighbours - multiple integers (neighbours) separated by spaces per line (ED)
  vector<vector<int>> neighbours(0);
  std::ifstream nei_file(data_dir + "Neighbours.txt");
  while (getline(nei_file, line))
  {
    std::stringstream ss(line);
    std::string n;
    vector<int> nei(0);
    while (getline(ss, n, ' ')) nei.push_back(stoi(n));
    neighbours.push_back(nei);
  }
  nei_file.close();
  // read counties - one integer (county) per line (ED)
  vector<int> counties(0);
  std::ifstream cou_file(data_dir + "County.txt");
  while (getline(cou_file, line)) counties.push_back(stoi(line));
  cou_file.close();

  // seats per constituency - second command line argument
  std::stringstream ss(argv[2]);
  vector<int> seats(0);
  while (getline(ss, line, ',')) seats.push_back(stoi(line));
  std::sort(seats.begin(), seats.end());
  // initialising map
  Map map(seats, populations, neighbours, counties);
  // storing the initial map configuration
  vector<int> init = map.config();
  // coupling constants - third command line argument
  ss.clear();
  ss.str("");
  ss.str(argv[3]);
  vector<std::string> J_str({"1"});
  vector<double> J_vec({1.});
  while (getline(ss, line, ','))
  {
    J_str.push_back(line);
    J_vec.push_back(stod(line));
  }
  valarray<double> J(J_vec.data(), J_vec.size());
  // getting Hamiltonian normalisations (such that 0 <= H_P, H_C, H_D, H_B <= 1 and 0 <= H <= sum(Js) to make coupling tuning easier)
  valarray<double> Z = {
    // max(H_P): all EDs assigned to smallest-seat constituency
    // i.e population variance of smallest constituency = abs(total seats - constituency seats) / (constituency seats) = (total seats) / (constituency seats) - 1
    // and population variance of each other constituency = abs(-constituency seats) / (constituency seats) = 1
    // so max(H_P) = total/smallest - 1 + (Q - 1) = total/smallest + Q - 2
    double(map.total_seats()) / map.seat(0) + map.Q() - 2.,
    // max(H_C): no ED is connected to another ED in the same constituency, i.e. number of disconnected parts = number of EDs
    double(map.EDs()),
    // max(H_D): same case as max(H_C), i.e. all neighbours of each ED are in a different constituency
    double(map.borders()),
    // max(H_B): each constituency's EDs evenly spread across all counties
    // i.e. for each constituency, (number of EDs in constituency) - (number of EDs in main county) = (number of constituency's EDs in each county) * (total number of counties - 1) / (total number of counties) are not in primary county
    // adding this for each constituency gives below
    map.EDs() * (map.counties() - 1.) / map.counties()
  };
  // incorporating Hamiltonian normalisations into coupling constants
  valarray<double> J_Z = J/Z;
  // fixing county boundary coupling to 0 if map is wholly within a county
  if (map.counties() == 1)
  {
    J[3] = J_Z[3] = 0.;
    std::cout << "County boundary coupling set to 0\n";
  }

  // getting maximum population and number of neighbours
  int max_pop = *std::max_element(populations.begin(), populations.end());
  int max_nei = 0;
  for (int x = 0; x < map.EDs(); x ++) if (map.nei(x).size() > max_nei) max_nei = map.nei(x).size();
  // choosing the starting temperature - defined as temperature at which the highest energy increase is accepted with at least 99% probability
  // i.e. alpha = exp(-sum(J_i * H_i / Z_i) / T), rearrange for T and set H_i = max(H_i), alpha = 0.99
  valarray<double> max_deltaH = {
    // max(deltaH_P): smallest-seat constituency is already under-represented and loses the map's most populated ED to the next smallest constituency which was already over-represented
    // i.e. abs(-max_pop/(smallest desired seats)) + abs(max_pop/(next smallest desired seats)) = max_pop/(av_pop*seats[0]) + max_pop/(av_pop*seats[1])
    (max_pop / map.av_pop()) * (1./map.seat(0) + 1./map.seat(1)),
    // max(deltaH_C): removing from current constituency splits all neighbours into disconnected regions, adding to new constituency creates a new disconnected region
    // note: in most cases only floor(neighbours/2) can be made disconnected but there are some edge cases with neighbours with only one neighbour (e.g. islands) so this is an upper bound
    max_nei + 1.,
    // max(deltaH_D): changing constituency of highest-neighbour ED when all of its neighbours are in the same constituency
    double(max_nei),
    // max(deltaH_B): 0 if contained within a county, 1 otherwise (increasing number of EDs in non-primary county)
    std::min(map.counties() - 1., 1.)
  };
  double alpha = .99;
  double T = -(J_Z * max_deltaH).sum() / log(alpha);
  vector<double> Ts(0);
  // temperature cooling factor
  double cool = .9;
  // number of measured and discarded sweeps
  ss.clear();
  ss.str("");
  ss.str(argv[4]);
  getline(ss, line, ',');
  int N = stoi(line);
  getline(ss, line, ',');
  int N_disc = stoi(line);

  // vectors for each Hamiltonian at each temperature (sample means, sample variances, autocorrelation time estimators, and their corresponding errors)
  vector<vector<double>> Hs(J.size(), vector<double>(0)), H_errs(J.size(), vector<double>(0)), H_vars(J.size(), vector<double>(0)), H_var_errs(J.size(), vector<double>(0)), H_taus(J.size(), vector<double>(0)), H_tau_errs(J.size(), vector<double>(0));
  // same as above but for linear combination of Hamiltonians (i.e. what the MCMCSA algorithm minimises)
  vector<double> H_sums(0), H_sum_errs(0), H_sum_vars(0), H_sum_var_errs(0), H_sum_taus(0), H_sum_tau_errs(0);
  // same as above but for acceptance rate
  vector<double> accs(0), acc_errs(0), acc_vars(0), acc_var_errs(0), acc_taus(0), acc_tau_errs(0);
  // vector for runtime at each temperature
  vector<double> times(0);

  // variables for determining ground state degeneracy (set of optimal configurations)
  double H_min = J.sum();
  std::set<vector<int>> optimal_configs;
  int num_optimal_configs;
  bool continue_annealing;

  // looping over temperatures
  do
  {
    // recording start time
    auto start = std::chrono::steady_clock::now();

    // getting new temperature
    Ts.push_back(T);
    std::cout << Ts.size() << " " << T << "\n";

    // overall Hamiltonian coefficients (coupling + normalisation + temperature) and Hamiltonian tally
    valarray<double> J_ZT = J_Z / T, H(J.size());
    // thermalising/equilibrising
    for (int n = 0; n < N_disc; n ++) map.GS_Sweep(H, J_ZT);

    // getting Hamiltonians at start of measured iterations
    H = map.H();
    // Markov chains for Hamiltonians and acceptance rates
    vector<vector<double>> H_chain(J.size(), vector<double>(N));
    vector<double> H_sum_chain(N), acc_chain(N);
    // boolean for continuing/ending simulated annealing
    continue_annealing = false;
    // number of optimal configurations before sweeps
    num_optimal_configs = optimal_configs.size();

    // performing sweeps
    for (int n = 0; n < N; n ++)
    {
      // getting acceptance rates and Hamiltonians for measured iterations
      acc_chain[n] = map.GS_Sweep(H, J_ZT);
      for (int i = 0; i < J.size(); i ++) H_chain[i][n] = H[i];
      H_sum_chain[n] = (J_Z*H).sum();

      // updating set of optimal configurations and ensuring another annealing iteration if new lowest energy found
      if (H_sum_chain[n] < H_min)
      {
        H_min = H_sum_chain[n];
        optimal_configs = { map.config() };
        continue_annealing = true;
      }
      else
      {
        // otherwise adding optimal configuration if same energy as lowest energy found
        if (H_sum_chain[n] == H_min) optimal_configs.insert(map.config());
        // and ensuring another annealing iteration if total Hamiltonian is not constant
        if (n > 0 && H_sum_chain[n] != H_sum_chain[n-1]) continue_annealing = true;
      }
    }

    // ensuring another annealing iteration if more optimal configurations found during this iteration
    if (optimal_configs.size() > num_optimal_configs) continue_annealing = true;

    // stats stuff for each Hamiltonian - averages, errors, and autocorrelations
    for (int i = 0; i < J.size(); i ++) Markov_chain_calculations(H_chain[i], Hs[i], H_errs[i], H_vars[i], H_var_errs[i], H_taus[i], H_tau_errs[i]);

    // same as above but for total Hamiltonian and acceptance rate
    Markov_chain_calculations(H_sum_chain, H_sums, H_sum_errs, H_sum_vars, H_sum_var_errs, H_sum_taus, H_sum_tau_errs);
    Markov_chain_calculations(acc_chain, accs, acc_errs, acc_vars, acc_var_errs, acc_taus, acc_tau_errs);

    // getting runtime
    auto finish = std::chrono::steady_clock::now();
    times.push_back(std::chrono::duration_cast<std::chrono::milliseconds>(finish - start).count());

    // annealing
    T *= cool;
  }
  // continuing annealing procedure if required
  while (continue_annealing);

  // printing everything to .csv
  std::string save_dir = data_dir + std::to_string(map.total_seats()) + "_" + std::to_string(map.Q()) + "/";
  std::string filename = std::to_string(map.seat(0));
  for (int q = 1; q < seats.size(); q ++) filename += "," + std::to_string(map.seat(q));
  filename += "_" + J_str[0];
  for (int j = 1; j < J_str.size(); j ++) filename += "," + J_str[j];
  auto now = std::chrono::system_clock::now();
  auto seconds = std::chrono::duration_cast<std::chrono::seconds>(now.time_since_epoch());
  filename += "_" + std::to_string(seconds.count());
  std::ofstream file;
  file.open(save_dir + filename + ".csv");
  // seats, measured & discarded sweeps, coupling constants, Hamiltonian normalisations
  file << "Q";
  for (int q = 0; q < seats.size(); q ++) file << "," << map.seat(q);
  file << "\nN," << N << "," << N_disc << "\n";
  file << "J";
  for (int j = 0; j < J_str.size(); j ++) file << "," << J_str[j];
  file << "\nZ";
  for (int z = 0; z < Z.size(); z ++) file << "," << Z[z];
  // initial (randomised) configuration
  file << "\ninitial\n" << init.front();
  for (int x = 1; x < map.EDs(); x ++) file << "," << init[x];
  // optimal configurations - total Hamiltonian for all, individual Hamiltonians for each
  file << "\noptimals," << H_min;
  for (vector<int> config : optimal_configs)
  {
    map.change_config(config);
    valarray<double> H = map.H();
    file << "\nH";
    for (int i = 0; i < J.size(); i ++) file << "," << H[i];
    file << "\n" << config.front();
    for (int x = 1; x < config.size(); x ++) file << "," << config[x];
  }

  // all data vs temperature
  file << "\nT,HP,HP_err,HP_var,HP_var_err,HP_tau,HP_tau_err,HC,HC_err,HC_var,HC_var_err,HC_tau,HC_tau_err,HD,HD_err,HD_var,HD_var_err,HD_tau,HD_tau_err,HB,HB_err,HB_var,HB_var_err,HB_tau,HB_tau_err,H,H_err,H_var,H_var_err,H_tau,H_tau_err,acc,acc_err,acc_var,acc_var_err,acc_tau,acc_tau_err,time\n";
  for (int t = 0; t < Ts.size(); t ++)
  {
    file << Ts[t] << ",";
    for (int i = 0; i < J.size(); i ++) file << Hs[i][t] << "," << H_errs[i][t] << "," << H_vars[i][t] << "," << H_var_errs[i][t] << "," << H_taus[i][t] << "," << H_tau_errs[i][t] << ",";
    file << H_sums[t] << "," << H_sum_errs[t] << "," << H_sum_vars[t] << "," << H_sum_var_errs[t] << "," << H_sum_taus[t] << "," << H_sum_tau_errs[t] << ",";
    file << accs[t] << "," << acc_errs[t] << "," << acc_vars[t] << "," << acc_var_errs[t] << "," << acc_taus[t] << "," << acc_tau_errs[t] << ",";
    file << times[t] << "\n";
  }
  file.close();

  return 0;
}
