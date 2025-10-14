#include <stdlib.h>
#include <iostream>
#include <fstream>
#include <sstream>
#include <string>
#include <valarray>
using std::valarray;
#include <chrono>
#include <omp.h>
#include "Map.h"
#include "statfuncs.h"


int main(int argc, char *argv[])
{
  // set the number of OpenMP threads to the max
  // TODO definitely change this: either take number as input or specify that it should be set in the command line
  int max = omp_get_max_threads();
  omp_set_num_threads(max);

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
  // red neighbours - multiple integers (neighbours) separated by spaces per line (ED)
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

  // number of groupings ("seats" for now while we're just doing single-seat stuff) - second command line argument
  int seats = atoi(argv[2]);
  // initialising map
  Map map(seats, populations, neighbours);
  // storing the initial map configuration
  vector<int> init = map.config();
  // coupling constants - third command line argument
  std::stringstream ss(argv[3]);
  vector<double> J_vec({1.});
  while (getline(ss, line, ',')) J_vec.push_back(stod(line));
  valarray<double> J(J_vec.data(), J_vec.size());
  // incorporating Hamiltonian normalisations into coupling constants
  valarray<double> J_Z = J/valarray<double>{ 2.*(map.Q()-1), 1.*map.EDs(), 1.*map.borders() };

  // getting maximum population and number of neighbours
  int max_pop = 0, max_nei = 0;
  for (int x = 0; x < map.EDs(); x ++)
  {
    if (map.pop(x) > max_pop) max_pop = map.pop(x);
    if (map.nei(x).size() > max_nei) max_nei = map.nei(x).size();
  }
  // choosing the starting temperature - defined as temperature at which the highest energy increase is accepted with 99% probability
  double max_T = -(valarray<double>{ 2.*max_pop/map.av_pop(), 1.*(1+max_nei/2), 1.*max_nei }*J_Z).sum()/log(.99);
  // getting annealing temperatures
  // TODO change this to instead stop algorithm after no more updates (instead of guessing a cold enough temperature)
  vector<double> Ts = { max_T };
  for (int t = 0; t < 150; t ++) Ts.push_back(Ts.back()*.9);
  // number of measured and discarded sweeps
  int N = 10000, N_disc = 1000;

  // vectors for storing observables & errors & autocorrelation times at each temperature
  vector<vector<double>> Hs(3, vector<double>(Ts.size())), H_errs(3, vector<double>(Ts.size())), H_taus(3, vector<double>(Ts.size())), H_tau_errs(3, vector<double>(Ts.size()));
  vector<double> H_sums(Ts.size()), H_sum_errs(Ts.size()), H_sum_taus(Ts.size()), H_sum_tau_errs(Ts.size());
  vector<double> times(Ts.size());
  vector<double> accs(Ts.size()), acc_errs(Ts.size()), acc_taus(Ts.size()), acc_tau_errs(Ts.size());

  // looping over temperatures
  for (int t = 0; t < Ts.size(); t ++)
  {
    // recording start time
    auto start = std::chrono::steady_clock::now();
    std::cout << t << "\n";

    // overall Hamiltonian coefficients (coupling + normalisation + temperature) and Hamiltonian tally
    valarray<double> J_ZT = J_Z / Ts[t], H(3);
    // thermalising/equilibrising
    for (int n = 0; n < N_disc; n ++) map.GS_Sweep(H, J_ZT);

    // getting Hamiltonians at start of measured iterations
    H = map.H();
    // Markov chains for Hamiltonians and acceptance rates
    vector<vector<double>> H_chain(3, vector<double>(N));
    vector<double> H_sum_chain(N), acc_chain(N);
    // getting acceptance rates and Hamiltonians for measured iterations
    for (int n = 0; n < N; n ++)
    {
      acc_chain[n] = map.GS_Sweep(H, J_ZT);
      for (int i = 0; i < 3; i ++) H_chain[i][n] = H[i];
      H_sum_chain[n] = (J_Z*H).sum();
    }

    // stats stuff for Hamiltonians - averages, errors, and autocorrelations
    for (int i = 0; i < 3; i ++)
    {
      Hs[i][t] = mean(H_chain[i]);
      autocorr(H_chain[i], Hs[i][t], H_taus[i][t], H_tau_errs[i][t]);
      H_errs[i][t] = mean_error(H_chain[i], Hs[i][t])*sqrt(H_taus[i][t]);
    }

    // same as above but for total Hamiltonian
    H_sums[t] = mean(H_sum_chain);
    autocorr(H_sum_chain, H_sums[t], H_sum_taus[t], H_sum_tau_errs[t]);
    H_sum_errs[t] = mean_error(H_sum_chain, H_sums[t])*sqrt(H_sum_taus[t]);

    // and again for acceptance rate
    accs[t] = mean(acc_chain);
    autocorr(acc_chain, accs[t], acc_taus[t], acc_tau_errs[t]);
    acc_errs[t] = mean_error(acc_chain, accs[t])*sqrt(acc_taus[t]);

    // getting runtime
    auto finish = std::chrono::steady_clock::now();
    times[t] = std::chrono::duration_cast<std::chrono::milliseconds>(finish - start).count();
  }

  // final configuration
  vector<int> fina = map.config();
  // printing everything to .csv
  // TODO for the love of God make this less cluttered
  std::ofstream file;
  file.open(data_dir + "configs.csv");
  // groupings, measured sweeps, discarded sweeps, coupling constants
  file << "Q," << map.Q() << ",N," << N_disc << "," << N;
  file << "\nJ," << J[0];
  for (int j = 1; j < J.size(); j ++) file << "," << J[j];
  // initial and final configurations
  file << "\ninit," << init.front();
  for (int x = 1; x < map.EDs(); x ++) file << "," << init[x];
  file << "\nfina," << fina.front();
  for (int x = 1; x < map.EDs(); x ++) file << "," << fina[x];
  // temperatures, time per temperature
  file << "\nT," << Ts.front();
  for (int t = 1; t < Ts.size(); t ++) file << "," << Ts[t];
  file << "\ntime," << times.front();
  for (int t = 1; t < Ts.size(); t ++) file << "," << times[t];
  // Hamiltonians & errors & autocorrelation times & errors
  file << "\nH";
  for (int i = 0; i < 3; i ++)
  {
    file << "\n" << Hs[i].front();
    for (int t = 1; t < Ts.size(); t ++) file << "," << Hs[i][t];
    file << "\n" << H_errs[i].front();
    for (int t = 1; t < Ts.size(); t ++) file << "," << H_errs[i][t];
    file << "\n" << H_taus[i].front();
    for (int t = 1; t < Ts.size(); t ++) file << "," << H_taus[i][t];
    file << "\n" << H_tau_errs[i].front();
    for (int t = 1; t < Ts.size(); t ++) file << "," << H_tau_errs[i][t];
  }
  // same for total Hamiltonian
  file << "\nH_sum\n" << H_sums.front();
  for (int t = 1; t < Ts.size(); t ++) file << "," << H_sums[t];
  file << "\n" << H_sum_errs.front();
  for (int t = 1; t < Ts.size(); t ++) file << "," << H_sum_errs[t];
  file << "\n" << H_sum_taus.front();
  for (int t = 1; t < Ts.size(); t ++) file << "," << H_sum_taus[t];
  file << "\n" << H_sum_tau_errs.front();
  for (int t = 1; t < Ts.size(); t ++) file << "," << H_sum_tau_errs[t];
  // same for acceptance rates
  file << "\nacc\n" << accs.front();
  for (int t = 1; t < Ts.size(); t ++) file << "," << accs[t];
  file << "\n" << acc_errs.front();
  for (int t = 1; t < Ts.size(); t ++) file << "," << acc_errs[t];
  file << "\n" << acc_taus.front();
  for (int t = 1; t < Ts.size(); t ++) file << "," << acc_taus[t];
  file << "\n" << acc_tau_errs.front();
  for (int t = 1; t < Ts.size(); t ++) file << "," << acc_tau_errs[t];
  file.close();

  return 0;
}