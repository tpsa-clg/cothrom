#include <iostream>
#include <fstream>
#include <sstream>
#include <vector>
#include <valarray>
#include <cmath>
#include <random>
#include <chrono>
#include <algorithm>
#include <omp.h>
using namespace std;

mt19937 r(1234);
uniform_real_distribution<double> standard_uniform(0., 1.);

class Map
{
  private:
    const int Q_;
    const vector<int> ED_pop_;
    const vector<vector<int>> ED_nei_;

    vector<int> ED_q_;

    int total_pop_, EDs_, borders_;
    double av_pop_;
    uniform_int_distribution<int> int_dist_;

    vector<double> q_pop_;
    vector<vector<vector<int>>> q_group_;

    vector<vector<int>> connect_(vector<int>& disconnected) const
    {
      vector<vector<int>> connected(0);
      while (disconnected.size())
      {
        vector<int> group = { disconnected.back() };
        disconnected.pop_back();
        int i = 0;
        while (i < group.size())
        {
          int x = group[i];
          for (int j = 0; j < ED_nei_[x].size(); j ++)
          {
            int y = ED_nei_[x][j];
            vector<int>::iterator it = find(disconnected.begin(), disconnected.end(), y);
            if (it != disconnected.end())
            {
              group.push_back(y);
              disconnected.erase(it);
            }
          }
          i ++;
        }
        connected.push_back(group);
      }
      return connected;
    }

    valarray<double> deltaH_curr_(const int& x, int& cqg_idx, vector<vector<int>>& cngs) const
    {
      int curr = ED_q_[x];

      vector<int> cxg;
      for (cqg_idx = 0; cqg_idx < q_group_[curr].size(); cqg_idx ++)
      {
        cxg = q_group_[curr][cqg_idx];
        vector<int>::iterator it = find(cxg.begin(), cxg.end(), x);
        if (it != cxg.end())
        {
          cxg.erase(it);
          break;
        }
      }
      cngs = connect_(cxg);

      int deltaHD_curr = 0;
      for (int i = 0; i < ED_nei_[x].size(); i ++) if (ED_q_[ED_nei_[x][i]] == curr) deltaHD_curr ++;

      return valarray<double>{ (abs(q_pop_[curr] - ED_pop_[x]) - abs(q_pop_[curr]))/av_pop_, abs(q_group_[curr].size() + cngs.size() - 2.) - q_group_[curr].size() + 1, double(deltaHD_curr) };
    }
    valarray<double> deltaH_prop_(const int& x, const int& prop, vector<int>& pqg_idxs, vector<vector<int>>& pngs) const
    {
      for (int i = 0; i < ED_nei_[x].size(); i ++)
      {
        int y = ED_nei_[x][i];
        if (ED_q_[y] == prop) for (int g = 0; g < q_group_[prop].size(); g ++) if (find(q_group_[prop][g].begin(), q_group_[prop][g].end(), y) != q_group_[prop][g].end())
        {
          if (find(pqg_idxs.begin(), pqg_idxs.end(), g) == pqg_idxs.end())
          {
            pqg_idxs.push_back(g);
            pngs.push_back(q_group_[prop][g]);
          }
          break;
        }
      }

      int deltaHD_prop = 0;
      for (int i = 0; i < ED_nei_[x].size(); i ++) if (ED_q_[ED_nei_[x][i]] == prop) deltaHD_prop --;

      return valarray<double>{ (abs(q_pop_[prop] + ED_pop_[x]) - abs(q_pop_[prop]))/av_pop_, q_group_[prop].size() - pngs.size() - abs(q_group_[prop].size() - 1.), double(deltaHD_prop) };
    }

    void config_update_()
    {
      fill(q_pop_.begin(), q_pop_.end(), -av_pop_);

      vector<vector<int>> disconnected(Q_, vector<int>(0));
      for (int x = 0; x < EDs_; x ++)
      {
        q_pop_[ED_q_[x]] += ED_pop_[x];
        disconnected[ED_q_[x]].push_back(x);
      }
      #pragma omp parallel for
      for (int q = 0; q < Q_; q ++) q_group_[q] = connect_(disconnected[q]);
    }
    void site_update_(const int& x, const int& prop, const int& cqg_idx, vector<vector<int>>& cngs, vector<int>& pqg_idxs, vector<vector<int>>& pngs)
    {
      int curr = ED_q_[x];
      ED_q_[x] = prop;

      q_pop_[curr] -= ED_pop_[x];
      q_pop_[prop] += ED_pop_[x];

      q_group_[curr][cqg_idx] = q_group_[curr].back();
      q_group_[curr].pop_back();
      q_group_[curr].insert(q_group_[curr].end(), make_move_iterator(cngs.begin()), make_move_iterator(cngs.end()));
      sort(pqg_idxs.begin(), pqg_idxs.end());
      vector<int> pxg = { x };
      for (int g = pqg_idxs.size()-1; g >= 0; g --)
      {
        q_group_[prop][pqg_idxs[g]] = q_group_[prop].back();
        q_group_[prop].pop_back();
        pxg.insert(pxg.end(), make_move_iterator(pngs[g].begin()), make_move_iterator(pngs[g].end()));
      }
      q_group_[prop].push_back(pxg);
    }
  public:
    Map(const int& constituencies, const vector<int>& populations, const vector<vector<int>>& neighbours) : Q_(constituencies), ED_pop_(populations), ED_nei_(neighbours), ED_q_(populations.size()), total_pop_(0), EDs_(populations.size()), borders_(0), int_dist_(0, constituencies-1), q_pop_(constituencies), q_group_(constituencies)
    {
      for (int x = 0; x < EDs_; x ++)
      {
        ED_q_[x] = int_dist_(r);
        total_pop_ += ED_pop_[x];
        borders_ += ED_nei_[x].size();
      }
      borders_ /= 2;
      av_pop_ = double(total_pop_) / double(Q_);

      config_update_();
    }

    int Q() const { return Q_; }
    int pop(const int& x) const { return ED_pop_[x]; }
    vector<int> nei(const int& x) const { return ED_nei_[x]; }
    vector<int> config() const { return ED_q_; }
    int EDs() const { return EDs_; }
    int borders() const { return borders_; }
    double av_pop() const { return av_pop_; }

    void change_config(const vector<int>& config)
    {
      ED_q_ = config;
      config_update_();
    }

    valarray<double> H() const
    {
      double HP = 0., HC = 0.;
      #pragma omp parallel for reduction(+:HP,HC)
      for (int q = 0; q < Q_; q ++)
      {
        HP += abs(q_pop_[q]);
        HC += abs(q_group_[q].size() - 1.);
      }
      int HD = 0;
      #pragma omp parallel for reduction(+:HD)
      for (int x = 0; x < EDs_; x ++) for (int i = 0; i < ED_nei_[x].size(); i ++) if (ED_q_[x] != ED_q_[ED_nei_[x][i]]) HD ++;
      return valarray<double>{ HP/av_pop_, HC, double(HD/2) };
    }

    int MA_Sweep(valarray<double>& H, const valarray<double>& J_ZT)
    {
      int alpha = 0;
      for (int x = 0; x < EDs_; x ++)
      {
        int prop;
        do { prop = int_dist_(r); } while (prop == ED_q_[x]);

        int cqg_idx;
        vector<vector<int>> cngs, pngs(0);
        vector<int> pqg_idxs(0);
        valarray<double> deltaH = deltaH_curr_(x, cqg_idx, cngs) + deltaH_prop_(x, prop, pqg_idxs, pngs);

        double deltaH_sum = (J_ZT*deltaH).sum();
        if (deltaH_sum <= 0 || standard_uniform(r) < exp(-deltaH_sum))
        {
          site_update_(x, prop, cqg_idx, cngs, pqg_idxs, pngs);
          H += deltaH;
          alpha ++;
        }
      }
      return alpha;
    }

    int GS_Sweep(valarray<double>& H, const valarray<double>& J_ZT)
    {
      int alpha = 0;
      for (int x = 0; x < EDs_; x ++)
      {
        int curr = ED_q_[x];
        int cqg_idx;
        vector<vector<int>> cngs, pqg_idxs(Q_, vector<int>(0));
        vector<vector<vector<int>>> pngs(Q_, vector<vector<int>>(0));
        vector<valarray<double>> deltaH(Q_, deltaH_curr_(x, cqg_idx, cngs));
        vector<double> prop_dist(Q_);
        #pragma omp parallel for
        for (int q = 0; q < Q_; q ++)
        {
          if (q != curr)
          {
            deltaH[q] += deltaH_prop_(x, q, pqg_idxs[q], pngs[q]);
            prop_dist[q] = exp(-(J_ZT*deltaH[q]).sum());
          }
          else
          {
            deltaH[q] = valarray<double>{ 0., 0., 0. };
            prop_dist[q] = 1.;
          }
        }
        discrete_distribution<int> Gibbs_dist(prop_dist.begin(), prop_dist.end());
        int prop = Gibbs_dist(r);
        
        if (prop != curr)
        {
          site_update_(x, prop, cqg_idx, cngs, pqg_idxs[prop], pngs[prop]);
          H += deltaH[prop];
          alpha ++;
        }
      }
      return alpha;
    }
};


double mean(const vector<double>& chain)
{
  double sum = 0.;
  #pragma omp parallel for reduction(+:sum)
  for (int n = 0; n < chain.size(); n ++) sum += chain[n];
  return sum/chain.size();
}
double quad_sum(const vector<double>& chain, const double& mu)
{
  double sum = 0.;
  #pragma omp parallel for reduction(+:sum)
  for (int n = 0; n < chain.size(); n ++) sum += pow(chain[n] - mu, 2.);
  return sum;
}
double mean_error(const vector<double>& chain, const double& mu)
{
  return sqrt(quad_sum(chain, mu) / (chain.size()*(chain.size()-1.)));
}

void autocorr(const vector<double>& chain, const double& mu, double& tau, double& deltatau)
{
  int N = chain.size(), M = 0;
  double fac = 2.*N/quad_sum(chain, mu);
  tau = 1.;
  do
  {
    M++;
    double sum = 0.;
    #pragma omp parallel for reduction(+:sum)
    for (int n = 0; n < N-M; n ++) sum += (chain[n]-mu)*(chain[n+M]-mu);
    tau += sum/(N-M)*fac;
  } while (M < 5*tau);
  deltatau = tau*sqrt((4.*M+2.)/N);
}
vector<double> thin(const vector<double>& chain, const int& tau)
{
  vector<double> thinned(chain.size()/tau);
  #pragma omp parallel for
  for (int n = 0; n < thinned.size(); n ++) thinned[n] = chain[n*tau];
  return thinned;
}


int main(int argc, char *argv[])
{
  int max = omp_get_max_threads();
  omp_set_num_threads(max);

  string constituency_name = argv[1];
  string line;
  vector<int> populations(0);
  ifstream pop_file(constituency_name + " populations.txt");
  while (getline(pop_file, line)) populations.push_back(stoi(line));
  pop_file.close();
  vector<vector<int>> neighbours(0);
  ifstream nei_file(constituency_name + " neighbours.txt");
  while (getline(nei_file, line))
  {
    stringstream ss(line);
    int n;
    vector<int> nei(0);
    while (ss >> n) nei.push_back(n);
    neighbours.push_back(nei);
  }
  nei_file.close();

  int seats = atoi(argv[2]);
  Map constituency(seats, populations, neighbours);
  vector<int> init = constituency.config();
  valarray<double> J = { 1., 2., 1. };
  valarray<double> J_Z = J/valarray<double>{ 2.*(constituency.Q()-1), 1.*constituency.EDs(), 1.*constituency.borders() };
  int max_pop = 0, max_nei = 0;
  for (int x = 0; x < constituency.EDs(); x ++)
  {
    if (constituency.pop(x) > max_pop) max_pop = constituency.pop(x);
    if (constituency.nei(x).size() > max_nei) max_nei = constituency.nei(x).size();
  }

  double max_T = -(valarray<double>{ 2.*max_pop/constituency.av_pop(), 1.*(1+max_nei/2), 1.*max_nei }*J_Z).sum()/log(.99);
  vector<double> Ts = { max_T };
  for (int t = 0; t < 150; t ++) Ts.push_back(Ts.back()*.9);
  int N = 10000, N_disc = 1000;

  vector<vector<double>> Hs(3, vector<double>(Ts.size())), H_errs(3, vector<double>(Ts.size())), H_taus(3, vector<double>(Ts.size())), H_tau_errs(3, vector<double>(Ts.size()));
  vector<double> H_sums(Ts.size()), H_sum_errs(Ts.size()), H_sum_taus(Ts.size()), H_sum_tau_errs(Ts.size());
  vector<double> times(Ts.size());
  vector<double> accs(Ts.size()), acc_errs(Ts.size()), acc_taus(Ts.size()), acc_tau_errs(Ts.size());

  for (int t = 0; t < Ts.size(); t ++)
  {
    auto start = chrono::steady_clock::now();
    cout << t << "\n";

    valarray<double> J_ZT = J_Z / Ts[t], H(3);
    for (int n = 0; n < N_disc; n ++) constituency.GS_Sweep(H, J_ZT);

    H = constituency.H();
    vector<vector<double>> H_chain(3, vector<double>(N));
    vector<double> H_sum_chain(N), acc_chain(N);
    for (int n = 0; n < N; n ++)
    {
      acc_chain[n] = constituency.GS_Sweep(H, J_ZT);
      for (int i = 0; i < 3; i ++) H_chain[i][n] = H[i];
      H_sum_chain[n] = (J_Z*H).sum();
    }

    for (int i = 0; i < 3; i ++)
    {
      Hs[i][t] = mean(H_chain[i]);
      autocorr(H_chain[i], Hs[i][t], H_taus[i][t], H_tau_errs[i][t]);
      H_errs[i][t] = mean_error(H_chain[i], Hs[i][t])*sqrt(H_taus[i][t]);
    }

    H_sums[t] = mean(H_sum_chain);
    autocorr(H_sum_chain, H_sums[t], H_sum_taus[t], H_sum_tau_errs[t]);
    H_sum_errs[t] = mean_error(H_sum_chain, H_sums[t])*sqrt(H_sum_taus[t]);

    accs[t] = mean(acc_chain);
    autocorr(acc_chain, accs[t], acc_taus[t], acc_tau_errs[t]);
    acc_errs[t] = mean_error(acc_chain, accs[t])*sqrt(acc_taus[t]);

    auto finish = chrono::steady_clock::now();
    times[t] = chrono::duration_cast<chrono::milliseconds>(finish - start).count();
  }

  vector<int> fina = constituency.config();
  ofstream file;
  file.open(constituency_name + " configs.csv");
  file << "Q," << constituency.Q() << ",N," << N_disc << "," << N;
  file << "\nJ," << J[0];
  for (int j = 1; j < J.size(); j ++) file << "," << J[j];
  file << "\ninit," << init.front();
  for (int x = 1; x < constituency.EDs(); x ++) file << "," << init[x];
  file << "\nfina," << fina.front();
  for (int x = 1; x < constituency.EDs(); x ++) file << "," << fina[x];
  file << "\nT," << Ts.front();
  for (int t = 1; t < Ts.size(); t ++) file << "," << Ts[t];
  file << "\ntime," << times.front();
  for (int t = 1; t < Ts.size(); t ++) file << "," << times[t];
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
  file << "\nH_sum\n" << H_sums.front();
  for (int t = 1; t < Ts.size(); t ++) file << "," << H_sums[t];
  file << "\n" << H_sum_errs.front();
  for (int t = 1; t < Ts.size(); t ++) file << "," << H_sum_errs[t];
  file << "\n" << H_sum_taus.front();
  for (int t = 1; t < Ts.size(); t ++) file << "," << H_sum_taus[t];
  file << "\n" << H_sum_tau_errs.front();
  for (int t = 1; t < Ts.size(); t ++) file << "," << H_sum_tau_errs[t];
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