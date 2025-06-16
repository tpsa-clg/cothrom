#include <math.h>
#include "statfuncs.h"

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