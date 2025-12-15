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

vector<vector<int>> Map::connect_(vector<int>& disconnected) const
{
  // disconnected: a list of EDs that we want to split into connected subsets, i.e. the contiguous parts

  // create an empty list of lists, where connected[i] will give the i-th connected subset of the input ED list
  vector<vector<int>> connected(0);
  // iterate until our list of EDs is empty, i.e. until we have assigned each ED to a connected subset
  while (not disconnected.empty())
  {
    // pick an arbitrary element of the remaining list of EDs - here we choose the last element of the list
    // we will then create the connected subset to which this ED belongs
    vector<int> group = { disconnected.back() };
    disconnected.pop_back();
    // iterate over EDs in connected subset (breadth-first) until no more neighbours can be added
    int i = 0;
    while (i < group.size())
    {
      int x = group[i];
      // iterate over ED's neighbours
      for (int j = 0; j < ED_nei_[x].size(); j ++)
      {
        int y = ED_nei_[x][j];
        // find location of neighbour in list of remaining EDs
        // if it == disconnected.end() then the neighbour is not in list (and thus is already in our connected subset list or was never in the original list of EDs)
        // otherwise we move it into our connected subset of EDs
        vector<int>::iterator it = std::find(disconnected.begin(), disconnected.end(), y);
        if (it != disconnected.end())
        {
          group.push_back(y);
          disconnected.erase(it);
        }
      }
      // move onto next ED in connected subset
      i ++;
    }
    // append this connected subset into our list of connected subsets
    connected.push_back(group);
  }
  return connected;
}
vector<int> Map::diff_neighbours_(const int& x) const
{
  vector<int> props(0);
  for (int y = 0; y < ED_nei_[x].size(); y ++)
  {
    int q = ED_q_[ED_nei_[x][y]];
    if (q != ED_q_[x]) props.push_back(q);
  }
  return props;
}

valarray<double> Map::deltaH_curr_(const int& x, int& cqg_idx, vector<vector<int>>& cngs) const
{
  // x: ED index
  // cqg_idx: index of x's connected subset in q_group_[curr]
  // cngs: the connected subsets that would result from removing x from its current constituency

  // current constituency of x
  int curr = ED_q_[x];

  // connected subset to which x belongs
  vector<int> cxg;
  // iterate over connected subsets until we locate the one containing x
  for (cqg_idx = 0; cqg_idx < q_group_[curr].size(); cqg_idx ++)
  {
    cxg = q_group_[curr][cqg_idx];
    // find index of x's connected subset and remove x
    // note that we are not updating any private variables
    vector<int>::iterator it = std::find(cxg.begin(), cxg.end(), x);
    if (it != cxg.end())
    {
      cxg.erase(it);
      break;
    }
  }
  // re-connect the remaining EDs into connected subsets
  cngs = connect_(cxg);

  // calculate the increase in the compactness Hamiltonian, i.e. the number of neighbours in x's constituency
  int deltaHD_curr = 0;
  for (int i = 0; i < ED_nei_[x].size(); i ++) if (ED_q_[ED_nei_[x][i]] == curr) deltaHD_curr ++;

  // calculate the decrease in the county boundary Hamiltonian, i.e. only if removing x from its constituency lessens a breach
  int deltaHB_curr = 0;
  vector<int> tmp_county_tally = q_cou_[curr];
  tmp_county_tally[ED_cou_[x]] --;
  if (tmp_county_tally[ED_cou_[x]] < *std::max_element(tmp_county_tally.begin(), tmp_county_tally.end())) deltaHB_curr --;

  // return the changes to the population, contiguity, and compactness Hamiltonians
  return valarray<double>{ (abs(q_pop_[curr] - ED_pop_[x]) - abs(q_pop_[curr]))/(seats_[curr] * av_pop_), fabs(q_group_[curr].size() + cngs.size() - 2.) - q_group_[curr].size() + 1, double(deltaHD_curr), double(deltaHB_curr) };
}
valarray<double> Map::deltaH_prop_(const int& x, const int& prop, vector<int>& pqg_idxs, vector<vector<int>>& pngs) const
{
  // pqg_idxs: indexes of x's neighbours' connected subsets in q_group_[prop]
  // pngs: connected subsets to which x's neighbours in the proposed constituency belong

  // iterate over neighbours of x
  for (int i = 0; i < ED_nei_[x].size(); i ++)
  {
    int y = ED_nei_[x][i];
    // if neighbour is in proposed constituency, find its connected subset
    if (ED_q_[y] == prop) for (int g = 0; g < q_group_[prop].size(); g ++) if (std::find(q_group_[prop][g].begin(), q_group_[prop][g].end(), y) != q_group_[prop][g].end())
    {
      // append connected subset (index + subset) to lists if we haven't already
      if (std::find(pqg_idxs.begin(), pqg_idxs.end(), g) == pqg_idxs.end())
      {
        pqg_idxs.push_back(g);
        pngs.push_back(q_group_[prop][g]);
      }
      break;
    }
  }

  // calculate the decrease in the compactness Hamiltonian, i.e. the number of neighbours in the proposed constituency
  int deltaHD_prop = 0;
  for (int i = 0; i < ED_nei_[x].size(); i ++) if (ED_q_[ED_nei_[x][i]] == prop) deltaHD_prop --;

  // calculate the increase in the county boundary Hamiltonian, i.e. if adding x to the proposed constituency worsens a breach
  int deltaHB_prop = 0;
  if (q_cou_[prop][ED_cou_[x]] != *std::max_element(q_cou_[prop].begin(), q_cou_[prop].end())) deltaHB_prop ++;

  // return the changes to the population, contiguity, and compactness Hamiltonians
  return valarray<double>{ double(abs(q_pop_[prop] + ED_pop_[x]) - abs(q_pop_[prop]))/(seats_[prop] * av_pop_), q_group_[prop].size() - pngs.size() - fabs(q_group_[prop].size() - 1.), double(deltaHD_prop), double(deltaHB_prop) };
}

void Map::config_update_()
{
  // re-initialise constituency populations and county tallies
  for (int q = 0; q < Q_; q ++) q_pop_[q] = -av_pop_ * seats_[q];
  q_cou_ = vector<vector<int>>(Q_, vector<int>(counties_, 0));

  // find each constituency's population, list of EDs, and county tally
  vector<vector<int>> disconnected(Q_, vector<int>(0));
  for (int x = 0; x < EDs_; x ++)
  {
    q_pop_[ED_q_[x]] += ED_pop_[x];
    disconnected[ED_q_[x]].push_back(x);
    q_cou_[ED_q_[x]][ED_cou_[x]] ++;
  }
  // find connected subsets for each constituency
  #pragma omp parallel for
  for (int q = 0; q < Q_; q ++) q_group_[q] = connect_(disconnected[q]);
}
void Map::site_update_(const int& x, const int& prop, const int& cqg_idx, vector<vector<int>>& cngs, vector<int>& pqg_idxs, vector<vector<int>>& pngs)
{
  // parameters as defined in deltaH_curr_() and deltaH_prop_()

  // get current constituency and update to proposed constituency
  int curr = ED_q_[x];
  ED_q_[x] = prop;

  // update constituency populations
  q_pop_[curr] -= ED_pop_[x];
  q_pop_[prop] += ED_pop_[x];

  // remove current connected subset
  q_group_[curr][cqg_idx] = q_group_[curr].back();
  q_group_[curr].pop_back();
  // insert new connected subsets (resulting from removing x from curr)
  q_group_[curr].insert(q_group_[curr].end(), make_move_iterator(cngs.begin()), make_move_iterator(cngs.end()));
  // remove connected subsets of neighbours in proposed constituency
  std::sort(pqg_idxs.begin(), pqg_idxs.end());
  vector<int> pxg = { x };
  for (int g = pqg_idxs.size()-1; g >= 0; g --)
  {
    q_group_[prop][pqg_idxs[g]] = q_group_[prop].back();
    q_group_[prop].pop_back();
    pxg.insert(pxg.end(), make_move_iterator(pngs[g].begin()), make_move_iterator(pngs[g].end()));
  }
  // add them back in but as one connected subset
  q_group_[prop].push_back(pxg);

  // update constituency county tallies
  q_cou_[curr][ED_cou_[x]] --;
  q_cou_[prop][ED_cou_[x]] ++;
}

Map::Map(const vector<int>& seats, const vector<int>& populations, const vector<vector<int>>& neighbours, const vector<int>& counties) : seats_(seats), ED_pop_(populations), ED_nei_(neighbours), ED_cou_(counties), ED_q_(populations.size()), total_pop_(std::reduce(ED_pop_.begin(), ED_pop_.end())), EDs_(populations.size()), borders_(0), counties_(*std::max_element(ED_cou_.begin(), ED_cou_.end())+1), Q_(seats.size()), total_seats_(std::reduce(seats_.begin(), seats_.end())), av_pop_(double(total_pop_) / double(total_seats_)), q_dist_(0, Q_-1), q_pop_(Q_), q_group_(Q_)
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
    for (int y = 0; y < ED_nei_[x].size(); y ++) neighbour_links[q].push_back(ED_nei_[x][y]);
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
      for (int y = 0; y < ED_nei_[x].size(); y ++) if (std::find(assigned_EDs.begin(), assigned_EDs.end(), ED_nei_[x][y]) == assigned_EDs.end() && std::find(neighbour_links[q].begin(), neighbour_links[q].end(), ED_nei_[x][y]) == assigned_EDs.end()) neighbour_links[q].push_back(ED_nei_[x][y]);
    }
  }

  // get number of borders
  for (int x = 0; x < EDs_; x ++) borders_ += ED_nei_[x].size();
  borders_ /= 2;

  // get constituency populations and connected subsets
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
  // tally each constituency's contribution to population, contiguity, and county boundary Hamiltonians
  double HP = 0.;
  int HC = 0, HB = EDs_;
  #pragma omp parallel for reduction(+:HP,HC,HB)
  for (int q = 0; q < Q_; q ++)
  {
    HP += abs(q_pop_[q]) / (seats_[q] * av_pop_);
    HC += abs(int(q_group_[q].size()) - 1);
    int tally = 0;
    // EDs in each constituency's primary county don't contribute to breaches
    HB -= *std::max_element(q_cou_[q].begin(), q_cou_[q].end());
  }
  // tally each ED's contribution to compactness Hamiltonian
  int HD = 0;
  #pragma omp parallel for reduction(+:HD)
  for (int x = 0; x < EDs_; x ++) for (int i = 0; i < ED_nei_[x].size(); i ++) if (ED_q_[x] != ED_q_[ED_nei_[x][i]]) HD ++;
  // return population, contigutiy, and compactness Hamiltonians
  return valarray<double>{ HP, double(HC), double(HD/2), double(HB) };
}

int Map::MA_Sweep(valarray<double>& H, const valarray<double>& J_ZT)
{
  // J_ZT: combination of coefficients for each Hamiltonian, i.e. (coupling constant) / (normalising factor * temperature)

  // acceptance rate
  int alpha = 0;
  // sweeping over all EDs
  for (int x = 0; x < EDs_; x ++)
  {
    // find x's neighbours' constituencies different to x's current constituencies
    vector<int> props = diff_neighbours_(x);
    // move to next ED if no neighbours in different constituency
    if (props.empty()) continue;
    // else choose proposal at random from neighbours' constituencies
    // TODO consider picking directly from set instead of from all constituencies until we get one in the list
    int prop;
    do { prop = q_dist_(r); } while (std::find(props.begin(), props.end(), prop) == props.end());

    // calculating the proposed change in each Hamiltonian
    int cqg_idx;
    vector<vector<int>> cngs, pngs(0);
    vector<int> pqg_idxs(0);
    valarray<double> deltaH = deltaH_curr_(x, cqg_idx, cngs) + deltaH_prop_(x, prop, pqg_idxs, pngs);

    // accepting/rejecting proposal
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
  // parameters as defined in MA_Sweep()

  // "acceptance" rate, i.e. fraction of changes in ED constituencies
  int alpha = 0;
  // sweeping over all EDs
  for (int x = 0; x < EDs_; x ++)
  {
    int curr = ED_q_[x];
    // find x's neighbours' constituencies different to x's current constituencies
    vector<int> props = diff_neighbours_(x);
    // move to next ED if no neighbours in different constituency
    if (props.empty()) continue;
    // else initialise vectors for deltaH_prop_() for all possible changes
    int cqg_idx;
    vector<vector<int>> cngs, pqg_idxs(Q_, vector<int>(0));
    vector<vector<vector<int>>> pngs(Q_, vector<vector<int>>(0));
    vector<valarray<double>> deltaH(Q_, deltaH_curr_(x, cqg_idx, cngs));
    vector<double> prop_dist(Q_);
    // get probabilities for each constituency change
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
        deltaH[q] += deltaH_prop_(x, q, pqg_idxs[q], pngs[q]);
        prop_dist[q] = exp(-(J_ZT*deltaH[q]).sum());
      }
    }
    // "propose" a new constituency based on calculated distribution
    int prop = std::discrete_distribution<int>(prop_dist.begin(), prop_dist.end())(r);

    // only need to update configuration if proposed and current constituencies are different
    if (prop != curr)
    {
      site_update_(x, prop, cqg_idx, cngs, pqg_idxs[prop], pngs[prop]);
      H += deltaH[prop];
      alpha ++;
    }
  }
  return alpha;
}
