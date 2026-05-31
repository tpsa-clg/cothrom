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
  // directory for reading populations, neighbours, configuration
  std::string data_dir = "data/" + map_name + "/";
  // read actual seats per constituency
  std::ifstream actual_in(data_dir + "actual.csv");
  std::string line;
  getline(actual_in, line);
  std::stringstream ss(line);
  std::string seat;
  vector<int> seats(0);
  while (getline(ss, seat, ',')) if (seat != "Q") seats.push_back(stoi(seat));
  // exit if Hamiltonians already added to csv
  getline(actual_in, line);
  actual_in.close();
  if (line[0] == 'H') return 0;
  // otherwise read configuration
  ss.clear();
  ss.str("");
  ss.str(line);
  vector<int> config(0);
  std::string q;
  while (getline(ss, q, ',')) config.push_back(stoi(q));

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

  // initialising map
  Map map(seats, populations, neighbours, counties);
  // setting actual configuration
  map.change_config(config);
  // getting Hamiltonians of actual configuration
  valarray<double> H = map.H();

  // overwriting actual csv to match format
  std::ofstream actual_out;
  actual_out.open(data_dir + "actual.csv");
  actual_out << "Q";
  for (int q = 0; q < seats.size(); q ++) actual_out << "," << seats[q];
  actual_out << "\nH";
  for (int i = 0; i < H.size(); i ++) actual_out << "," << H[i];
  actual_out << "\n" << config.front();
  for (int x = 1; x < config.size(); x ++) actual_out << "," << config[x];
  actual_out << "\n";
  actual_out.close();

  return 0;
}
