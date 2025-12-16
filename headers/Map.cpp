#include <valarray>
using std::valarray;
#include <math.h>
#include <algorithm>
#include <random>
#include <omp.h>
#include "Map.h"

// random number generator and standard uniform distribution
std::mt19937 r(1234);
std::uniform_real_distribution<double> standard_uniform(0., 1.);

bool Map::contiguous_after_removal_(const int& x) const
{
  // x: ED index

  // get neighbours of x in its current constituency
  int curr = ED_q_[x];
  vector<int> curr_nei(0);
  for (int n = 0; n < ED_nei_[x].size(); n ++)
  {
    int y = ED_nei_[x][n];
    if (ED_q_[y] == curr) curr_nei.push_back(y);
  }

  // contiguity broken if no neighbours in same constituency (and so removing x from its constituency erases constituency entirely) or all neighbours in x's constituency (and so changing x to another constituency creates a disconnected part for its new constituency)
  if (curr_nei.empty() || curr_nei.size() == ED_nei_[x].size()) return false;
  // contiguity not broken if x has only one neighbour in same constituency (and thus not connecting any regions together)
  else if (curr_nei.size() == 1) return true;

  // otherwise check if neighbours in same constituency remain connected after removing x
  else
  {
    // pick an arbitrary neighbour of x
    vector<int> connected = { curr_nei.back() };
    curr_nei.pop_back();
    // iterate through EDs connected to chosen neighbour
    int i = 0;
    while (i < connected.size())
    {
      int y = connected[i];
      // loop over neighbours of ED
      for (int i = 0; i < ED_nei_[y].size(); i ++)
      {
        int z = ED_nei_[y][i];
        // add neighbour to connected list if not x, if in same constituency, and if not already in connected list
        if (z != x && ED_q_[z] == curr && std::find(connected.begin(), connected.end(), z) == connected.end())
        {
          connected.push_back(z);
          vector<int>::iterator it = std::find(curr_nei.begin(), curr_nei.end(), z);
          if (it != curr_nei.end())
          {
            // remove x's neighbour from the list of its same-constituency neighbours if in connected list
            curr_nei.erase(it);
            // if all of x's neighbours are connected after removing x then constituency still contiguous
            if (curr_nei.empty()) return true;
          }
        }
      }
      i ++;
    }
    // if this stage is reached then curr_nei is not empty, and so not all of x's neighbours are connected after removing x
    return false;
  }
}
vector<int> Map::diff_neighbours_(const int& x) const
{
  vector<int> props(0);
  for (int i = 0; i < ED_nei_[x].size(); i ++)
  {
    int q = ED_q_[ED_nei_[x][i]];
    if (q != ED_q_[x]) props.push_back(q);
  }
  return props;
}

valarray<double> Map::deltaH_curr_(const int& x) const
{
  // x: ED index

  // current constituency of x
  int curr = ED_q_[x];

  // calculate the increase in the compactness Hamiltonian, i.e. the number of neighbours in x's constituency
  int deltaHD_curr = 0;
  for (int i = 0; i < ED_nei_[x].size(); i ++) if (ED_q_[ED_nei_[x][i]] == curr) deltaHD_curr ++;

  // calculate the decrease in the county boundary Hamiltonian, i.e. only if removing x from its constituency lessens a breach
  int deltaHB_curr = 0;
  vector<int> tmp_county_tally = q_cou_[curr];
  tmp_county_tally[ED_cou_[x]] --;
  if (tmp_county_tally[ED_cou_[x]] < *std::max_element(tmp_county_tally.begin(), tmp_county_tally.end())) deltaHB_curr --;

  // return the changes to the population and compactness Hamiltonians
  return valarray<double>{ (abs(q_pop_[curr] - ED_pop_[x]) - abs(q_pop_[curr]))/(seats_[curr] * av_pop_), double(deltaHD_curr), double(deltaHB_curr) };
}
valarray<double> Map::deltaH_prop_(const int& x, const int& prop) const
{
  // x: ED index
  // prop: proposed constituency for x

  // calculate the decrease in the compactness Hamiltonian, i.e. the number of neighbours in the proposed constituency
  int deltaHD_prop = 0;
  for (int i = 0; i < ED_nei_[x].size(); i ++) if (ED_q_[ED_nei_[x][i]] == prop) deltaHD_prop --;

  // calculate the increase in the county boundary Hamiltonian, i.e. if adding x to the proposed constituency worsens a breach
  int deltaHB_prop = 0;
  if (q_cou_[prop][ED_cou_[x]] != *std::max_element(q_cou_[prop].begin(), q_cou_[prop].end())) deltaHB_prop ++;

  // return the changes to the population and compactness Hamiltonians
  return valarray<double>{ double(abs(q_pop_[prop] + ED_pop_[x]) - abs(q_pop_[prop]))/(seats_[prop] * av_pop_), double(deltaHD_prop), double(deltaHB_prop) };
}

void Map::config_update_()
{
  // re-initialise constituency populations and county tallies
  for (int q = 0; q < Q_; q ++) q_pop_[q] = -av_pop_ * seats_[q];
  q_cou_ = vector<vector<int>>(Q_, vector<int>(counties_, 0));

  // find each constituency's population and county tally
  for (int x = 0; x < EDs_; x ++)
  {
    int q = ED_q_[x];
    q_pop_[q] += ED_pop_[x];
    q_cou_[q][ED_cou_[x]] ++;
  }
}
void Map::site_update_(const int& x, const int& prop)
{
  // parameters as defined in deltaH_curr_() and deltaH_prop_()

  // get current constituency and update to proposed constituency
  int curr = ED_q_[x];
  ED_q_[x] = prop;

  // update constituency populations
  int pop = ED_pop_[x];
  q_pop_[curr] -= pop;
  q_pop_[prop] += pop;

  // update constituency county tallies
  int cou = ED_cou_[x];
  q_cou_[curr][cou] --;
  q_cou_[prop][cou] ++;
}

Map::Map(const vector<int>& seats, const vector<int>& populations, const vector<vector<int>>& neighbours, const vector<int>& counties) : seats_(seats), ED_pop_(populations), ED_nei_(neighbours), ED_cou_(counties), ED_q_(populations.size()), total_pop_(std::reduce(ED_pop_.begin(), ED_pop_.end())), EDs_(populations.size()), borders_(0), counties_(*std::max_element(ED_cou_.begin(), ED_cou_.end())+1), Q_(seats.size()), total_seats_(std::reduce(seats_.begin(), seats_.end())), av_pop_(double(total_pop_) / double(total_seats_)), q_dist_(0, Q_-1), q_pop_(Q_)
{
  // seats: number of seats per constituency
  // populations/neighbours/counties: list of ED populations/neighbours/counties

  // initialise contiguous constituencies
  vector<int> assigned_EDs(0);
  vector<vector<int>> neighbour_links (Q_, vector<int>(0));
  // assign one ED to each constituency
  for (int q = 0; q < Q_; q ++)
  {
    int x = q * EDs_ / Q_;
    assigned_EDs.push_back(x);
    ED_q_[x] = q;
    for (int i = 0; i < ED_nei_[x].size(); i ++) neighbour_links[q].push_back(ED_nei_[x][i]);
  }
  // keep assigning EDs until all assigned
  while (assigned_EDs.size() < EDs_) for (int q = 0; q < Q_; q ++)
  {
    int x;
    vector<int>::iterator it;
    // loop through constituency's neighbours until one can be added to constituency or all already assigned
    while (it != assigned_EDs.end() && not neighbour_links[q].empty())
    {
      x = neighbour_links[q].back();
      neighbour_links[q].pop_back();
      it = std::find(assigned_EDs.begin(), assigned_EDs.end(), x);
    }
    // if neighbour isn't assigned yet then assign it
    if (it == assigned_EDs.end())
    {
      ED_q_[x] = q;
      assigned_EDs.push_back(x);
      // add new neighbours to list of EDs to check next, if not assigned or not already in list
      for (int i = 0; i < ED_nei_[x].size(); i ++)
      {
        int y = ED_nei_[x][i];
        if (std::find(assigned_EDs.begin(), assigned_EDs.end(), y) == assigned_EDs.end() && std::find(neighbour_links[q].begin(), neighbour_links[q].end(), y) == neighbour_links[q].end()) neighbour_links[q].push_back(y);
      }
    }
  }

  // get number of borders
  for (int x = 0; x < EDs_; x ++) borders_ += ED_nei_[x].size();
  borders_ /= 2;

  // get constituency populations and county tallies
  config_update_();
}

void Map::change_config(const vector<int>& config)
{
  // manually set the new configuration and make necessary changes
  ED_q_ = config;
  config_update_();
}

valarray<double> Map::H() const
{
  // tally each constituency's contribution to population and county boundary Hamiltonians
  double HP = 0.;
  int HB = EDs_;
  #pragma omp parallel for reduction(+:HP,HC,HB)
  for (int q = 0; q < Q_; q ++)
  {
    HP += abs(q_pop_[q]) / (seats_[q] * av_pop_);
    int tally = 0;
    // EDs in each constituency's primary county don't contribute to breaches
    HB -= *std::max_element(q_cou_[q].begin(), q_cou_[q].end());
  }
  // tally each ED's contribution to compactness Hamiltonian
  int HD = 0;
  #pragma omp parallel for reduction(+:HD)
  for (int x = 0; x < EDs_; x ++) for (int i = 0; i < ED_nei_[x].size(); i ++) if (ED_q_[x] != ED_q_[ED_nei_[x][i]]) HD ++;
  // return population, contigutiy, and compactness Hamiltonians
  return valarray<double>{ HP, double(HD/2), double(HB) };
}

int Map::MA_Sweep(valarray<double>& H, const valarray<double>& J_ZT)
{
  // H: Hamiltonian to be updated
  // J_ZT: combination of coefficients for each Hamiltonian, i.e. (coupling constant) / (normalising factor * temperature)

  // acceptance rate
  int alpha = 0;
  // sweeping over all EDs
  for (int x = 0; x < EDs_; x ++)
  {
    // move to next ED if removing x from its current constituency breaks contiguity
    if (not contiguous_after_removal_(x)) continue;
    // else choose proposal at random from neighbours' constituencies
    vector<int> props = diff_neighbours_(x);
    int prop;
    // TODO consider picking directly from set instead of from all constituencies until we get one in the list
    do { prop = q_dist_(r); } while (std::find(props.begin(), props.end(), prop) == props.end());

    // calculating the proposed change in each Hamiltonian
    valarray<double> deltaH = deltaH_curr_(x) + deltaH_prop_(x, prop);

    // accepting/rejecting proposal
    double deltaH_sum = (J_ZT*deltaH).sum();
    if (deltaH_sum <= 0 || standard_uniform(r) < exp(-deltaH_sum))
    {
      site_update_(x, prop);
      H += deltaH;
      alpha ++;
    }
  }
  return alpha;
}

int Map::GS_Sweep(valarray<double>& H, const valarray<double>& J_ZT)
{
  // parameters as defined in MA_Sweep()

  // "acceptance" rate, i.e. fraction of changes in ED constituencies
  int alpha = 0;
  // sweeping over all EDs
  for (int x = 0; x < EDs_; x ++)
  {
    // move to next ED if removing x from its current constituency breaks contiguity
    if (not contiguous_after_removal_(x)) continue;
    // else find x's neighbours' constituencies different to x's current constituencies
    vector<int> props = diff_neighbours_(x);
    // get probabilities for each possible constituency change
    int curr = ED_q_[x];
    vector<valarray<double>> deltaH(Q_, deltaH_curr_(x));
    vector<double> prop_dist(Q_);
    #pragma omp parallel for
    for (int q = 0; q < Q_; q ++)
    {
      // no need to calculate anything for "change" to current constituency
      if (q == curr) prop_dist[q] = 1.;
      // not possible to change to non-neighbouring constituency
      else if (std::find(props.begin(), props.end(), q) == props.end()) prop_dist[q] = 0.;
      // otherwise calculate change in Hamiltonians & corresponding distribution weight
      else
      {
        deltaH[q] += deltaH_prop_(x, q);
        prop_dist[q] = exp(-(J_ZT*deltaH[q]).sum());
      }
    }
    // "propose" a new constituency based on calculated distribution
    int prop = std::discrete_distribution<int>(prop_dist.begin(), prop_dist.end())(r);

    // only need to update configuration if proposed and current constituencies are different
    if (prop != curr)
    {
      site_update_(x, prop);
      H += deltaH[prop];
      alpha ++;
    }
  }
  return alpha;
}
