#ifndef STATFUNCS_H
#define STATFUNCS_H

#include <vector>
using std::vector;

double mean(const vector<double>& chain);
double quad_sum(const vector<double>& chain, const double& mu);
double mean_error(const vector<double>& chain, const double& mu);

void autocorr(const vector<double>& chain, const double& mu, double& tau, double& deltatau);
vector<double> thin(const vector<double>& chain, const int& tau);

#endif
