#include <stdlib.h>
#include <iostream>
#include <fstream>
#include <sstream>
#include <string>
#include <valarray>
using std::valarray;
#include <chrono>
#include <omp.h>
#include <set>
#include <cmath>
#include "headers\Map.h" //Changed to include full path
#include "headers\statfuncs.h" //Changed to include full path


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
  // initialising map
  Map map(seats, populations, neighbours, counties);
  // storing the initial map configuration
  vector<int> init = map.config();
  // coupling constants - third command line argument
  ss.clear();
  ss.str("");
  ss.str(argv[3]);
  vector<double> J_vec({1.});
  while (getline(ss, line, ',')) J_vec.push_back(stod(line));
  valarray<double> J(J_vec.data(), J_vec.size());
  // incorporating Hamiltonian normalisations into coupling constants
  valarray<double> Z = { 2.*(map.total_seats() - *std::min_element(seats.begin(), seats.end())), double(map.EDs()), double(map.borders()), map.EDs()*(map.counties()-1.)/map.counties() };
  // compute J/Z safely to avoid 0/0 -> NaN
  valarray<double> J_Z(J.size());
  for (size_t i = 0; i < J.size(); i++)
  {
    if (Z[i] == 0.)
    {
      if (J[i] == 0.) J_Z[i] = 0.;
      else
      {
        std::cerr << "Error: nonzero coupling J[" << i << "]=" << J[i] << " for zero normalisation Z[" << i << "]\n";
        return 1;
      }
    }
    else J_Z[i] = J[i] / Z[i];
  }

  // getting maximum population and number of neighbours
  int max_pop = 0, max_nei = 0;
  for (int x = 0; x < map.EDs(); x ++)
  {
    if (map.pop(x) > max_pop) max_pop = map.pop(x);
    if (map.nei(x).size() > max_nei) max_nei = map.nei(x).size();
  }
  // choosing the starting temperature - defined as temperature at which the highest energy increase is accepted with 99% probability
  valarray<double> worst_inc = { 2.*max_pop/map.av_pop(), 1.+max_nei/2., double(max_nei), 1. };
  double numerator = -(worst_inc * J_Z).sum();
  double denom = log(.99);
  double T = numerator / denom;
  if (std::isnan(T) || std::isinf(T))
  {
    std::cerr << "Computed invalid initial temperature T; diagnostics:\n";
    std::cerr << "J:";
    for (size_t i = 0; i < J.size(); i++) std::cerr << " " << J[i];
    std::cerr << "\nZ:";
    for (size_t i = 0; i < Z.size(); i++) std::cerr << " " << Z[i];
    std::cerr << "\nJ_Z:";
    for (size_t i = 0; i < J_Z.size(); i++) std::cerr << " " << J_Z[i];
    std::cerr << "\nworst_inc:";
    for (size_t i = 0; i < worst_inc.size(); i++) std::cerr << " " << worst_inc[i];
    std::cerr << "\nnumerator=" << numerator << ", denom=" << denom << "\n";
    return 1;
  }
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
  std::ofstream file;
  // TODO save parameters in filename
  file.open(data_dir + "configs.csv");
  // seats, measured & discarded sweeps, coupling constants, Hamiltonian normalisations
  file << "Q";
  for (int q = 0; q < seats.size(); q ++) file << "," << map.seat(q);
  file << "\nN," << N << "," << N_disc << "\n";
  file << "J";
  for (int j = 0; j < J.size(); j ++) file << "," << J[j];
  file << "\nZ";
  for (int z = 0; z < Z.size(); z ++) file << "," << Z[z];
  // initial and optimal configurations
  file << "\ninitial\n" << init.front();
  for (int x = 1; x < map.EDs(); x ++) file << "," << init[x];
  file << "\noptimals";
  for (vector<int> config : optimal_configs)
  {
    file << "\n" << config[0];
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
