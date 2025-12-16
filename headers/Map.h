#ifndef MAP_H
#define MAP_H

#include <vector>
using std::vector;

// Custom class for electoral maps.
class Map
{
  private:
    /* INPUTS */
    // Number of seats per constituency.
    const vector<int> seats_;
    // Population of each ED.
    const vector<int> ED_pop_;
    // Neighbours of each ED.
    // Integers represent index in the given population/neighbour/county lists.
    const vector<vector<int>> ED_nei_;
    // Counties of each ED.
    // Integers represent (arbitrary) county labels.
    const vector<int> ED_cou_;

    /* OUTPUTS */
    // Constituency assigned to each electoral division, i.e. the configuration of our map.
    // Integers represent index in the given list of seats per constituency.
    vector<int> ED_q_;

    /* FIXED PARAMETERS*/
    // Total population, number of EDs, number of borders between EDs, and number of counties.
    int total_pop_, EDs_, borders_, counties_;
    // Number of constituencies, number of seats, and average population per seat.
    int Q_, total_seats_;
    double av_pop_;
    // Uniform distribution over constituency number.
    // Used to propose a constituency at random for the Metropolis algorithm.
    std::uniform_int_distribution<int> q_dist_;

    /* DYNAMIC PARAMETERS*/
    // Population of each constituency (minus ideal population, i.e. average population per constituency * number of seats in constituency).
    vector<double> q_pop_;
    // Tally of number of EDs in each county for each constituency.
    vector<vector<int>> q_cou_;

    // Test if removing an ED from its current constituency breaks contiguity.
    // Note: a constituency is considered to be non-contiguous if it does not exist.
    bool contiguous_after_removal_(const int& x) const;

    // Return the neighbouring constituencies of an ED different to its current constituency.
    vector<int> diff_neighbours_(const int& x) const;

    // Return the change to each Hamiltonian by changing an ED's constituency (from the current constituency/to a proposed constituency).
    valarray<double> deltaH_curr_(const int& x) const;
    valarray<double> deltaH_prop_(const int& x, const int& prop) const;

    // Update constituency populations and county tallies.
    // Only used at construction and manual configuration changes.
    void config_update_();

    // Update an ED's constituency and make corresponding population changes.
    // Used after each acceptance in the MCMC algorithms.
    void site_update_(const int& x, const int& prop);
  public:
    // Class constructor.
    Map(const vector<int>& seats, const vector<int>& populations, const vector<vector<int>>& neighbours, const vector<int>& counties);

    // Return private variables.
    int seat(const int& q) const { return seats_[q]; }
    int pop(const int& x) const { return ED_pop_[x]; }
    vector<int> nei(const int& x) const { return ED_nei_[x]; }
    vector<int> config() const { return ED_q_; }
    int total_pop() const { return total_pop_; }
    int EDs() const { return EDs_; }
    int borders() const { return borders_; }
    int counties() const { return counties_; }
    int Q() const { return Q_; }
    int total_seats() const { return total_seats_; }
    double av_pop() const { return av_pop_; }

    // Globally update a map's configuration.
    // Note: make sure the given configuration is contiguous, as there is currently no check for this!
    void change_config(const vector<int>& config);

    // Return each (unnormalised) Hamiltonian term of the current configuration.
    valarray<double> H() const;

    // Perform a single Metropolis algorithm sweep, update the Hamiltonian accordingly, and return the acceptance rate.
    int MA_Sweep(valarray<double>& H, const valarray<double>& J_ZT);

    // Perform a single Gibbs sampler (heat bath) sweep, update the Hamiltonian accordingly, and return the "acceptance" rate (how often an ED is changed).
    int GS_Sweep(valarray<double>& H, const valarray<double>& J_ZT);
};

#endif
