#include <cmath>
#include <cstdlib>
#include <algorithm>
#include <numeric>
#include <random>
#include <omp.h>
#include "Map.h"

// random number generator and standard uniform distribution
std::mt19937 r(1234);
std::uniform_real_distribution<double> standard_uniform(0., 1.);

// Minimum number of constituencies (Q_) at which parallelising the per-site
// Gibbs loop over constituencies is worth its OpenMP fork/join cost. Below this
// the loop runs serially: Q_ is small for area-scale runs and the loop executes
// once per ED per sweep, so at small Q_ the fork/join overhead dominates the
// tiny per-constituency work. Conservative default - tune per target/benchmark.
static constexpr int GS_PARALLEL_MIN_Q = 32;

vector<vector<int>> Map::connect_(const vector<int>& disconnected) const
{
  // disconnected: a list of EDs that we want to split into connected subsets, i.e. the contiguous parts

  // Membership bitmap over ED indices (dense in [0, EDs_)): present[x] == 1 iff x
  // is still an unassigned member of the input set. This replaces the old linear
  // std::find / erase over `disconnected` (which made the whole routine O(k^2))
  // with O(1) membership tests, giving overall O(k + edges).
  //
  // It is thread_local because connect_() is called concurrently from the
  // parallel loop in config_update_(). The bitmap is kept all-zero between calls
  // (every ED we mark below is unmarked again as it is absorbed into a subset),
  // so it can be reused across calls without re-allocating or re-clearing.
  static thread_local vector<char> present;
  if (int(present.size()) < EDs_) present.assign(EDs_, 0);

  // mark every ED currently in the set as present
  for (int x : disconnected) present[x] = 1;

  // create an empty list of lists, where connected[i] will give the i-th connected subset of the input ED list
  vector<vector<int>> connected(0);
  // use the original list as the source of (arbitrary) seeds; any ED not yet
  // absorbed into an earlier subset starts a new one
  for (int seed : disconnected)
  {
    if (not present[seed]) continue;
    // create the connected subset to which this seed belongs
    vector<int> group = { seed };
    present[seed] = 0;
    // iterate over EDs in connected subset (breadth-first) until no more neighbours can be added
    for (size_t i = 0; i < group.size(); i ++)
    {
      int x = group[i];
      // iterate over ED's neighbours; move any still-present neighbour into this subset
      for (int y : ED_nei_[x])
      {
        if (present[y])
        {
          present[y] = 0;
          group.push_back(y);
        }
      }
    }
    // append this connected subset into our list of connected subsets
    connected.push_back(std::move(group));
  }
  return connected;
}

Ham Map::deltaH_curr_(const int& x, int& cqg_idx, vector<vector<int>>& cngs) const
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

  // calculate the decrease in the county boundary Hamiltonian, i.e. only if removing x from its constituency lessens a breach.
  // Removing x lowers county cx's tally by one; the breach count is (EDs in constituency) - (largest county group),
  // so removing x lessens a breach iff cx is not the sole-largest group, i.e. iff some OTHER county holds at least
  // as many EDs: max_{c != cx} q_cou_[curr][c] >= q_cou_[curr][cx]. Computed in one pass, avoiding the old per-site
  // heap copy of the whole tally vector.
  int deltaHB_curr = 0;
  int cx = ED_cou_[x];
  int max_other = 0;
  for (int c = 0; c < counties_; c ++) if (c != cx && q_cou_[curr][c] > max_other) max_other = q_cou_[curr][c];
  if (max_other >= q_cou_[curr][cx]) deltaHB_curr --;

  // return the changes to the population, contiguity, and compactness Hamiltonians
  return Ham{ (std::fabs(q_pop_[curr] - ED_pop_[x]) - std::fabs(q_pop_[curr]))/(seats_[curr] * av_pop_), std::fabs(q_group_[curr].size() + cngs.size() - 2.) - q_group_[curr].size() + 1, double(deltaHD_curr), double(deltaHB_curr) };
}
Ham Map::deltaH_prop_(const int& x, const int& prop, vector<int>& pqg_idxs, vector<vector<int>>& pngs) const
{
  // pqg_idxs: indexes of x's neighbours' connected subsets in q_group_[prop]
  // pngs: connected subsets to which x's neighbours in the proposed constituency belong

  // iterate over neighbours of x
  for (int i = 0; i < ED_nei_[x].size(); i ++)
  {
    int y = ED_nei_[x][i];
    // if neighbour is in proposed constituency, find its connected subset
    if (ED_q_[y] == prop) for (int g = 0; g < q_group_[prop].size(); g ++)
    {
      vector<int> group = q_group_[prop][g];
      if (std::find(group.begin(), group.end(), y) != group.end())
      {
        // append connected subset (index + subset) to lists if we haven't already
        if (std::find(pqg_idxs.begin(), pqg_idxs.end(), g) == pqg_idxs.end())
        {
          pqg_idxs.push_back(g);
          pngs.push_back(group);
        }
        break;
      }
    }
  }

  // calculate the decrease in the compactness Hamiltonian, i.e. the number of neighbours in the proposed constituency
  int deltaHD_prop = 0;
  for (int i = 0; i < ED_nei_[x].size(); i ++) if (ED_q_[ED_nei_[x][i]] == prop) deltaHD_prop --;

  // calculate the increase in the county boundary Hamiltonian, i.e. if adding x to the proposed constituency worsens a breach
  int deltaHB_prop = 0;
  if (q_cou_[prop][ED_cou_[x]] != *std::max_element(q_cou_[prop].begin(), q_cou_[prop].end())) deltaHB_prop ++;

  // return the changes to the population, contiguity, and compactness Hamiltonians
  return Ham{ (std::fabs(q_pop_[prop] + ED_pop_[x]) - std::fabs(q_pop_[prop]))/(seats_[prop] * av_pop_), q_group_[prop].size() - pngs.size() - std::fabs(q_group_[prop].size() - 1.), double(deltaHD_prop), double(deltaHB_prop) };
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

Map::Map(const vector<int>& seats, const vector<int>& populations, const vector<vector<int>>& neighbours, const vector<int>& counties) : seats_(seats), ED_pop_(populations), ED_nei_(neighbours), ED_cou_(counties), ED_q_(populations.size()), total_pop_(std::reduce(ED_pop_.begin(), ED_pop_.end())), EDs_(populations.size()), borders_(0), counties_(*std::max_element(ED_cou_.begin(), ED_cou_.end())+1), Q_(seats.size()), total_seats_(std::reduce(seats_.begin(), seats_.end())), av_pop_(double(total_pop_) / total_seats_), int_dist_(0, Q_-1), q_pop_(Q_), q_group_(Q_)
{
  // seats: number of seats per constituency
  // populations/neighbours/counties: list of ED populations/neighbours/counties

  // randomly assign ED constituencies, get number of borders
  for (int x = 0; x < EDs_; x ++)
  {
    ED_q_[x] = int_dist_(r);
    borders_ += ED_nei_[x].size();
  }
  borders_ /= 2;

  // get constituency populations, connected subsets, and county tallies
  config_update_();
}

void Map::change_config(const vector<int>& config)
{
  // manually set the new configuration and make necessary changes
  ED_q_ = config;
  config_update_();
}

Ham Map::H() const
{
  // tally each constituency's contribution to population, contiguity, and county boundary Hamiltonians
  double HP = 0.;
  int HC = 0, HB = EDs_;
  #pragma omp parallel for reduction(+:HP,HC,HB)
  for (int q = 0; q < Q_; q ++)
  {
    HP += std::fabs(q_pop_[q]) / (seats_[q] * av_pop_);
    HC += std::abs(int(q_group_[q].size()) - 1);
    int tally = 0;
    // EDs in each constituency's primary county don't contribute to breaches
    HB -= *std::max_element(q_cou_[q].begin(), q_cou_[q].end());
  }
  // tally each ED's contribution to compactness Hamiltonian
  int HD = 0;
  #pragma omp parallel for reduction(+:HD)
  for (int x = 0; x < EDs_; x ++) for (int i = 0; i < ED_nei_[x].size(); i ++) if (ED_q_[x] != ED_q_[ED_nei_[x][i]]) HD ++;
  // return population, contiguity, and compactness Hamiltonians
  return Ham{ HP, double(HC), HD/2., double(HB) };
}

int Map::MA_Sweep(Ham& H, const Ham& J_ZT)
{
  // J_ZT: combination of coefficients for each Hamiltonian, i.e. (coupling constant) / (normalising factor * temperature)

  // acceptance rate
  int alpha = 0;
  // sweeping over all EDs
  for (int x = 0; x < EDs_; x ++)
  {
    // proposing a constituency different to x's current constituency
    int prop;
    do { prop = int_dist_(r); } while (prop == ED_q_[x]);

    // calculating the proposed change in each Hamiltonian
    int cqg_idx;
    vector<vector<int>> cngs, pngs(0);
    vector<int> pqg_idxs(0);
    Ham deltaH = deltaH_curr_(x, cqg_idx, cngs) + deltaH_prop_(x, prop, pqg_idxs, pngs);

    // accepting/rejecting proposal
    double deltaH_sum = sum(J_ZT*deltaH);
    if (deltaH_sum <= 0 || standard_uniform(r) < std::exp(-deltaH_sum))
    {
      site_update_(x, prop, cqg_idx, cngs, pqg_idxs, pngs);
      H += deltaH;
      alpha ++;
    }
  }
  return alpha;
}

int Map::GS_Sweep(Ham& H, const Ham& J_ZT)
{
  // parameters as defined in MA_Sweep()

  // "acceptance" rate, i.e. fraction of changes in ED constituencies
  int alpha = 0;
  // sweeping over all EDs
  for (int x = 0; x < EDs_; x ++)
  {
    int curr = ED_q_[x];
    // initialising vectors for deltaH_prop_() for all possible changes
    int cqg_idx;
    vector<vector<int>> cngs, pqg_idxs(Q_, vector<int>(0));
    vector<vector<vector<int>>> pngs(Q_, vector<vector<int>>(0));
    vector<Ham> deltaH(Q_, deltaH_curr_(x, cqg_idx, cngs));
    vector<double> prop_dist(Q_);
    // iterating over all constituencies
    // Parallelise only when Q_ is large enough to amortise fork/join (see
    // GS_PARALLEL_MIN_Q); serial otherwise. Each iteration writes only its own
    // q-indexed slots and deltaH_prop_ is const, so the loop is data-race free.
    #pragma omp parallel for if(Q_ >= GS_PARALLEL_MIN_Q)
    for (int q = 0; q < Q_; q ++)
    {
      // calculate change in Hamiltonians & corresponding distribution weight for each possible change
      if (q != curr)
      {
        deltaH[q] += deltaH_prop_(x, q, pqg_idxs[q], pngs[q]);
        prop_dist[q] = std::exp(-sum(J_ZT*deltaH[q]));
      }
      // no need to calculate "change" to current constituency
      else
      {
        deltaH[q] = Ham{ 0., 0., 0., 0. };
        prop_dist[q] = 1.;
      }
    }
    // "propose" a new constituency based on calculated distribution
    std::discrete_distribution<int> Gibbs_dist(prop_dist.begin(), prop_dist.end());
    int prop = Gibbs_dist(r);

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
