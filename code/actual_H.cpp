#include <stdlib.h>
#include <fstream>
#include <sstream>
#include <string>
#include <valarray>
using std::valarray;
#include "Map.h"

int main(int argc, char *argv[])
{
  // custom name for area of consideration - command line argument
  std::string map_name = argv[1];
  // directory for reading population & neighbour data and saving configs
  std::string data_dir = "data/" + map_name + "/";

  std::string line;
  // read populations - one integer (population) per line (electoral division)
  vector<int> populations(0);
  std::ifstream pop_file(data_dir + "Population.txt");
  while (getline(pop_file, line)) populations.push_back(stoi(line));
  pop_file.close();
  // read neighbours - multiple integers (neighbours) separated by spaces per line (ED)
  vector<vector<int>> neighbours(0);
  std::ifstream nei_file(data_dir + "Neighbours.txt");
  while (getline(nei_file, line))
  {
    std::stringstream ss(line);
    std::string n;
    vector<int> nei(0);
    while (getline(ss, n, ' ')) nei.push_back(stoi(n));
    neighbours.push_back(nei);
  }
  nei_file.close();
  // read counties - one integer (county) per line (ED)
  vector<int> counties(0);
  std::ifstream cou_file(data_dir + "County.txt");
  while (getline(cou_file, line)) counties.push_back(stoi(line));
  cou_file.close();

  // read actual seats per constituency and configuration
  std::fstream actual_file(data_dir + "actual.csv", std::fstream::in | std::fstream::out | std::fstream::app);
  getline(actual_file, line);
  std::stringstream ss(line);
  std::string s;
  vector<int> seats(0);
  while (getline(ss, s, ',')) if (s != "Q") seats.push_back(stoi(s));
  getline(actual_file, line);
  ss.clear();
  ss.str("");
  ss.str(line);
  vector<int> config(0);
  std::string q;
  while (getline(ss, q, ',')) config.push_back(stoi(q));

  // initialising map
  Map map(seats, populations, neighbours, counties);
  // setting actual configuration
  map.change_config(config);
  // getting Hamiltonians of actual configuration
  valarray<double> H = map.H();
  // appending Hamiltonian to csv
  actual_file << "H," << H[0];
  for (int i = 1; i < H.size(); i ++) actual_file << "," << H[i];
  actual_file << "\n";
  actual_file.close();

  return 0;
}
