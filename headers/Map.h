#ifndef MAP_H
#define MAP_H

#include <vector>
using std::vector;

class Map
{
  private:
    const int Q_;
    const vector<int> ED_pop_;
    const vector<vector<int>> ED_nei_;

    vector<int> ED_q_;

    int total_pop_, EDs_, borders_;
    double av_pop_;
    std::uniform_int_distribution<int> int_dist_;

    vector<double> q_pop_;
    vector<vector<vector<int>>> q_group_;

    vector<vector<int>> connect_(vector<int>& disconnected) const;

    valarray<double> deltaH_curr_(const int& x, int& cqg_idx, vector<vector<int>>& cngs) const;
    valarray<double> deltaH_prop_(const int& x, const int& prop, vector<int>& pqg_idxs, vector<vector<int>>& pngs) const;

    void config_update_();
    void site_update_(const int& x, const int& prop, const int& cqg_idx, vector<vector<int>>& cngs, vector<int>& pqg_idxs, vector<vector<int>>& pngs);
  public:
    Map(const int& constituencies, const vector<int>& populations, const vector<vector<int>>& neighbours);

    int Q() const { return Q_; }
    int pop(const int& x) const { return ED_pop_[x]; }
    vector<int> nei(const int& x) const { return ED_nei_[x]; }
    vector<int> config() const { return ED_q_; }
    int EDs() const { return EDs_; }
    int borders() const { return borders_; }
    double av_pop() const { return av_pop_; }

    void change_config(const vector<int>& config);

    valarray<double> H() const;

    int MA_Sweep(valarray<double>& H, const valarray<double>& J_ZT);

    int GS_Sweep(valarray<double>& H, const valarray<double>& J_ZT);
};

#endif
