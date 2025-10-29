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

  // seats per constituency - second command line argument
  std::stringstream ss(argv[2]);
  vector<int> seats(0);
  while (getline(ss, line, ',')) seats.push_back(stoi(line));
  // initialising map
  Map map(seats, populations, neighbours);
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
  // TODO change the population normalisation - currently for single-seat constituencies
  valarray<double> J_Z = J/valarray<double>{ 2.*(map.Q()-1), double(map.EDs()), double(map.borders()) };

  // getting maximum population and number of neighbours
  int max_pop = 0, max_nei = 0;
  for (int x = 0; x < map.EDs(); x ++)
  {
    if (map.pop(x) > max_pop) max_pop = map.pop(x);
    if (map.nei(x).size() > max_nei) max_nei = map.nei(x).size();
  }
  // choosing the starting temperature - defined as temperature at which the highest energy increase is accepted with 99% probability
  double T = -(valarray<double>{ 2.*max_pop/map.av_pop(), 1.+max_nei/2., double(max_nei) }*J_Z).sum()/log(.99);
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

  // vectors for storing observables & errors & autocorrelation times at each temperature
  vector<vector<double>> Hs(3, vector<double>(0)), H_errs(3, vector<double>(0)), H_taus(3, vector<double>(0)), H_tau_errs(3, vector<double>(0));
  vector<double> H_sums(0), H_sum_errs(0), H_sum_taus(0), H_sum_tau_errs(0);
  vector<double> times(0);
  vector<double> accs(0), acc_errs(0), acc_taus(0), acc_tau_errs(0);

  // looping over temperatures
  T /= cool;  
  do
  {
    // recording start time
    auto start = std::chrono::steady_clock::now();

    // getting new temperature
    T *= cool;
    Ts.push_back(T);
    std::cout << Ts.size() << " " << T << "\n";

    // overall Hamiltonian coefficients (coupling + normalisation + temperature) and Hamiltonian tally
    valarray<double> J_ZT = J_Z / T, H(3);
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
    // TODO probably use a function for this...
    double tau, deltatau;
    for (int i = 0; i < 3; i ++)
    {
      Hs[i].push_back(mean(H_chain[i]));
      autocorr(H_chain[i], Hs[i].back(), tau, deltatau);
      H_taus[i].push_back(tau);
      H_tau_errs[i].push_back(deltatau);
      H_errs[i].push_back(mean_error(H_chain[i], Hs[i].back())*sqrt(H_taus[i].back()));
    }

    // same as above but for total Hamiltonian
    H_sums.push_back(mean(H_sum_chain));
    autocorr(H_sum_chain, H_sums.back(), tau, deltatau);
    H_sum_taus.push_back(tau);
    H_sum_tau_errs.push_back(deltatau);
    H_sum_errs.push_back((mean_error(H_sum_chain, H_sums.back())*sqrt(H_sum_taus.back())));

    // and again for acceptance rate
    accs.push_back(mean(acc_chain));
    autocorr(acc_chain, accs.back(), tau, deltatau);
    acc_taus.push_back(tau);
    acc_tau_errs.push_back(deltatau);
    acc_errs.push_back(mean_error(acc_chain, accs.back())*sqrt(acc_taus.back()));

    // getting runtime
    auto finish = std::chrono::steady_clock::now();
    times.push_back(std::chrono::duration_cast<std::chrono::milliseconds>(finish - start).count());
  }
  // finish annealing when no new states have been accepted
  while (accs.back() >= 1. / double(N));

  // final configuration
  vector<int> final = map.config();
  // printing everything to .csv
  std::ofstream file;
  // TODO save parameters in filename
  file.open(data_dir + "configs.csv");
  // seats, measured & discarded sweeps, coupling constants
  file << "Q";
  for (int q = 0; q < seats.size(); q ++) file << "," << map.seat(q);
  file << "\nN," << N << "," << N_disc << "\n";
  file << "J";
  for (int j = 0; j < J.size(); j ++) file << "," << J[j];
  // initial and final configurations
  file << "\ninit";
  for (int x = 0; x < map.EDs(); x ++) file << "," << init[x];
  file << "\nfinal";
  for (int x = 0; x < map.EDs(); x ++) file << "," << final[x];
  // all data vs temperature
  // TODO loop over column titles instead of hardcoding
  file << "\nT,HP,HP_err,HP_tau,HP_tau_err,HC,HC_err,HC_tau,HC_tau_err,HD,HD_err,HD_tau,HD_tau_err,H,H_err,H_tau,H_tau_err,acc,acc_err,acc_tau,acc_tau_err,time\n";
  for (int t = 0; t < Ts.size(); t ++)
  {
    file << Ts[t] << ",";
    for (int i = 0; i < 3; i ++) file << Hs[i][t] << "," << H_errs[i][t] << "," << H_taus[i][t] << "," << H_tau_errs[i][t] << ",";
    file << H_sums[t] << "," << H_sum_errs[t] << "," << H_sum_taus[t] << "," << H_sum_tau_errs[t] << ",";
    file << accs[t] << "," << acc_errs[t] << "," << acc_taus[t] << "," << acc_tau_errs[t] << ",";
    file << times[t] << "\n";
  }

  return 0;
}
