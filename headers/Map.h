#ifndef MAP_H
#define MAP_H

#include <vector>
using std::vector;

// Custom class for electoral maps.
class Map
{
  private:
    /* INPUTS */
    // Number of groupings of electoral divisions.
    // This will be constituencies in the full-scale problem.
    const int Q_;
    // Population and neighbours of each ED.
    // Integers represent positions in the given population/neighbour lists.
    const vector<int> ED_pop_;
    const vector<vector<int>> ED_nei_;

    /* OUTPUTS */
    // Grouping assigned to each electoral division, i.e. the configuration of our map.
    vector<int> ED_q_;

    /* FIXED PARAMETERS*/
    // Total population, number of EDs, and number of borders between EDs.
    int total_pop_, EDs_, borders_;
    // Average population per grouping.
    double av_pop_;
    // Uniform distribution over grouping number.
    // Used to propose a grouping at random for the Metropolis algorithm.
    std::uniform_int_distribution<int> int_dist_;

    /* DYNAMIC PARAMETERS*/
    // Population of each grouping (minus average population per grouping).
    vector<double> q_pop_;
    // Connected subsets of each grouping.
    // A grouping is contiguous when it has one connected subset.
    vector<vector<vector<int>>> q_group_;

    // Return a vector of (geographically) connected subsets from a vector of EDs.
    // Note: input vector will be empty at return.
    // Also note: the ordering of subsets, and within each subset, is arbitrary.
    vector<vector<int>> connect_(vector<int>& disconnected) const;

    // Return the change to each Hamiltonian by changing an ED's grouping allocation (from the current grouping/to a proposed grouping).
    // Also returns (by reference) some relevant quantities for site_update_().
    valarray<double> deltaH_curr_(const int& x, int& cqg_idx, vector<vector<int>>& cngs) const;
    valarray<double> deltaH_prop_(const int& x, const int& prop, vector<int>& pqg_idxs, vector<vector<int>>& pngs) const;

    // Update grouping populations & connected subsets.
    // Only used at construction and manual configuration changes.
    void config_update_();

    // Update an ED's grouping allocation and makes corresponding population & connected subset changes.
    // Used after each acceptance in the MCMC algorithms.
    void site_update_(const int& x, const int& prop, const int& cqg_idx, vector<vector<int>>& cngs, vector<int>& pqg_idxs, vector<vector<int>>& pngs);
  public:
    // Class constructor.
    Map(const int& constituencies, const vector<int>& populations, const vector<vector<int>>& neighbours);

    // Return private variables.
    int Q() const { return Q_; }
    int pop(const int& x) const { return ED_pop_[x]; }
    vector<int> nei(const int& x) const { return ED_nei_[x]; }
    vector<int> config() const { return ED_q_; }
    int EDs() const { return EDs_; }
    int borders() const { return borders_; }
    double av_pop() const { return av_pop_; }

    // Globally update a map's configuration.
    void change_config(const vector<int>& config);

    // Return each (unnormalised) Hamiltonian term of the current configuration.
    valarray<double> H() const;

    // Perform a single Metropolis algorithm sweep and return the acceptance rate.
    int MA_Sweep(valarray<double>& H, const valarray<double>& J_ZT);

    // Perform a single Gibbs sampler (heat bath) sweep and return the "acceptance" rate (how often an ED is changed).
    int GS_Sweep(valarray<double>& H, const valarray<double>& J_ZT);
};

#endif
