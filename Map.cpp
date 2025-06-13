#include <valarray>
using std::valarray;
#include <math.h>
#include <algorithm>
#include <random>
#include <omp.h>
#include "Map.h"

std::mt19937 r(1234);
std::uniform_real_distribution<double> standard_uniform(0., 1.);

vector<vector<int>> Map::connect_(vector<int>& disconnected) const
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
        vector<int>::iterator it = std::find(disconnected.begin(), disconnected.end(), y);
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

valarray<double> Map::deltaH_curr_(const int& x, int& cqg_idx, vector<vector<int>>& cngs) const
{
  int curr = ED_q_[x];

  vector<int> cxg;
  for (cqg_idx = 0; cqg_idx < q_group_[curr].size(); cqg_idx ++)
  {
    cxg = q_group_[curr][cqg_idx];
    vector<int>::iterator it = std::find(cxg.begin(), cxg.end(), x);
    if (it != cxg.end())
    {
      cxg.erase(it);
      break;
    }
  }
  cngs = connect_(cxg);

  int deltaHD_curr = 0;
  for (int i = 0; i < ED_nei_[x].size(); i ++) if (ED_q_[ED_nei_[x][i]] == curr) deltaHD_curr ++;

  return valarray<double>{ (abs(q_pop_[curr] - ED_pop_[x]) - abs(q_pop_[curr]))/av_pop_, fabs(q_group_[curr].size() + cngs.size() - 2.) - q_group_[curr].size() + 1, double(deltaHD_curr) };
}
valarray<double> Map::deltaH_prop_(const int& x, const int& prop, vector<int>& pqg_idxs, vector<vector<int>>& pngs) const
{
  for (int i = 0; i < ED_nei_[x].size(); i ++)
  {
    int y = ED_nei_[x][i];
    if (ED_q_[y] == prop) for (int g = 0; g < q_group_[prop].size(); g ++) if (std::find(q_group_[prop][g].begin(), q_group_[prop][g].end(), y) != q_group_[prop][g].end())
    {
      if (std::find(pqg_idxs.begin(), pqg_idxs.end(), g) == pqg_idxs.end())
      {
        pqg_idxs.push_back(g);
        pngs.push_back(q_group_[prop][g]);
      }
      break;
    }
  }

  int deltaHD_prop = 0;
  for (int i = 0; i < ED_nei_[x].size(); i ++) if (ED_q_[ED_nei_[x][i]] == prop) deltaHD_prop --;

  return valarray<double>{ (abs(q_pop_[prop] + ED_pop_[x]) - abs(q_pop_[prop]))/av_pop_, q_group_[prop].size() - pngs.size() - fabs(q_group_[prop].size() - 1.), double(deltaHD_prop) };
}

void Map::config_update_()
{
  std::fill(q_pop_.begin(), q_pop_.end(), -av_pop_);

  vector<vector<int>> disconnected(Q_, vector<int>(0));
  for (int x = 0; x < EDs_; x ++)
  {
    q_pop_[ED_q_[x]] += ED_pop_[x];
    disconnected[ED_q_[x]].push_back(x);
  }
  #pragma omp parallel for
  for (int q = 0; q < Q_; q ++) q_group_[q] = connect_(disconnected[q]);
}
void Map::site_update_(const int& x, const int& prop, const int& cqg_idx, vector<vector<int>>& cngs, vector<int>& pqg_idxs, vector<vector<int>>& pngs)
{
  int curr = ED_q_[x];
  ED_q_[x] = prop;

  q_pop_[curr] -= ED_pop_[x];
  q_pop_[prop] += ED_pop_[x];

  q_group_[curr][cqg_idx] = q_group_[curr].back();
  q_group_[curr].pop_back();
  q_group_[curr].insert(q_group_[curr].end(), make_move_iterator(cngs.begin()), make_move_iterator(cngs.end()));
  std::sort(pqg_idxs.begin(), pqg_idxs.end());
  vector<int> pxg = { x };
  for (int g = pqg_idxs.size()-1; g >= 0; g --)
  {
    q_group_[prop][pqg_idxs[g]] = q_group_[prop].back();
    q_group_[prop].pop_back();
    pxg.insert(pxg.end(), make_move_iterator(pngs[g].begin()), make_move_iterator(pngs[g].end()));
  }
  q_group_[prop].push_back(pxg);
}

Map::Map(const int& constituencies, const vector<int>& populations, const vector<vector<int>>& neighbours) : Q_(constituencies), ED_pop_(populations), ED_nei_(neighbours), ED_q_(populations.size()), total_pop_(0), EDs_(populations.size()), borders_(0), int_dist_(0, constituencies-1), q_pop_(constituencies), q_group_(constituencies)
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

void Map::change_config(const vector<int>& config)
{
  ED_q_ = config;
  config_update_();
}

valarray<double> Map::H() const
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

int Map::MA_Sweep(valarray<double>& H, const valarray<double>& J_ZT)
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

int Map::GS_Sweep(valarray<double>& H, const valarray<double>& J_ZT)
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
    std::discrete_distribution<int> Gibbs_dist(prop_dist.begin(), prop_dist.end());
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
