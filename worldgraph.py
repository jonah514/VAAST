'''
*This file is a class which can instantiate and read "worldgraphs", essentially graphs of nodes which can be traversed for the purpose of trajectory prediction
*A new graph can be instantiated with an empty string as a parameter
*A file from a previous graph can be read in by putting the file path in the string
*Graphs can predict trajectory with the predict_trajectory function
'''

import geopy as gp
from geopy.distance import geodesic as gd
from geopy.geocoders import Nominatim
from geopy.geocoders import Photon
import networkx as nx
import pandas as pd
import json

#MUST BE MULTIPLES OF 90
#SET TO WHATEVER YOU WANT THE RESOLUTION TO BE
LAT_NODE_DIST = 0.5
LON_NODE_DIST = 0.5


class WorldGraph:
    
    def read_graph(self, filestring):
        filearr = filestring.split('\n')
        nodes_to_add = set()
        edges_to_add = []
        graphtoreturn = nx.Graph()
        #iterate through lines
        for i in range(len(filearr)):
            filearr[i] = filearr[i].split('_')
        #split up by delimeter
        for i in range(len(filearr)):
            #instantiate nodes for all these
            if len(filearr[i]) == 3:
                node1 = eval(filearr[i][0])
                node2 = eval(filearr[i][1])
                nodes_to_add.add(node1)
                nodes_to_add.add(node2)
                edges_to_add.append([node1, node2, float(filearr[i][2])])
        for i in nodes_to_add:
            graphtoreturn.add_node(i)
        graphtoreturn.add_weighted_edges_from(edges_to_add)
        #add them all
        return graphtoreturn
                

    def __init__(self, path : str, lat_dist = LAT_NODE_DIST, lon_dist = LON_NODE_DIST):
        self.lat_dist = lat_dist
        self.lon_dist = lon_dist
        self.airport_list = dict()
        #load in the airport list
        with open("static/airportsIATA.json","r") as f:
            self.airport_list = json.load(f)
        f.close()
        #create new one
        if path == '' or path is None:
            self.create_new()
        else:
            rawtext = ''
            #read in
            with open(path, 'r') as file:
                rawtext = file.read()
            self.graph = self.read_graph(rawtext)
            file.close()

    def predict_trajectory(self, location, airport : str):
        #heuristic
        def geodesic_heuristic(u, v):
            return gd(u, v).km
        #if an airport is supplied
        if type(location) == str:
            if airport not in self.airport_list.keys():
                print("Error, origin airport not recognized!")
                return
            else:
                self.graph.add_node((float(self.airport_list[location]['lat']), float(self.airport_list[location]['lon'])))
                location = (float(self.airport_list[location]['lat']), float(self.airport_list[location]['lon']))
        #if a lat/lon tuple is supplied
        else:
            #current position
            self.graph.add_node(location)
        if airport not in self.airport_list.keys():
            print("Error, airport not recognized!")
            return
        #destination position
        dest = (float(self.airport_list[airport]['lat']), float(self.airport_list[airport]['lon']))
        self.graph.add_node(dest)

        #connect the current position
        base_node_lat = (int(location[0]) // self.lat_dist) * self.lat_dist
        base_node_lon = (int(location[1]) // self.lon_dist) * self.lon_dist

        to_connect = []

        #below left
        to_connect.append([location, (base_node_lat, base_node_lon), gd(location, (base_node_lat, base_node_lon)).km])
        #below right
        to_connect.append([location, (base_node_lat, base_node_lon + self.lon_dist), gd(location, (base_node_lat, base_node_lon + self.lon_dist)).km])
        #above left
        to_connect.append([location, (base_node_lat + self.lat_dist, base_node_lon), gd(location, (base_node_lat + self.lat_dist, base_node_lon)).km])
        #above right
        to_connect.append([location, (base_node_lat + self.lat_dist, base_node_lon + self.lon_dist), gd(location, (base_node_lat + self.lat_dist, base_node_lon + self.lon_dist)).km])
        #SAME PROCESS FOR AIRPORT
        #connect the current position
        base_node_lat = (int(dest[0]) // self.lat_dist) * self.lat_dist
        base_node_lon = (int(dest[1]) // self.lon_dist) * self.lon_dist

        #below left
        to_connect.append([dest, (base_node_lat, base_node_lon), gd(dest, (base_node_lat, base_node_lon)).km])
        #below right
        to_connect.append([dest, (base_node_lat, base_node_lon + self.lon_dist), gd(dest, (base_node_lat, base_node_lon + self.lon_dist)).km])
        #above left
        to_connect.append([dest, (base_node_lat + self.lat_dist, base_node_lon), gd(dest, (base_node_lat + self.lat_dist, base_node_lon)).km])
        #above right
        to_connect.append([dest, (base_node_lat + self.lat_dist, base_node_lon + self.lon_dist), gd(dest, (base_node_lat + self.lat_dist, base_node_lon + self.lon_dist)).km])
        
        
        #connect everything
        self.graph.add_weighted_edges_from(to_connect)
        print(location)
        print(str(list(self.graph.neighbors(location))))
        print(dest)
        #print((52,0))
        #print(str(list(self.graph.neighbors((52,0)))))
        print(str(list(self.graph.neighbors(dest))))

        #return nx.astar_path(self.graph, location, dest, geodesic_heuristic, "weight")
        return nx.dijkstra_path(self.graph, location, dest)
        #return nx.dijkstra_path(self.graph, location, dest, weight="weight")
    
    def create_new(self):
        edges_to_add = []
        geolocator = Nominatim(user_agent="VAAST")
        #banned_countries = ["Afghanistan", "Belarus", "Iran", "Iraq", "North Korea", "Libya", "Mali", "Россия", "Somalia", "Syria", "Ukraine", "Venezuela", "Yemen"]
        banned_countries = ["افغانستان", "Беларусь", "ایران", "العراق", "조선민주주의인민공화국", "ليبيا", "Mali", "Россия","Soomaaliya الصومال", "سورية", "Україна", "Venezuela", "اليمن"]
        self.graph = nx.Graph()
        def scan_country(country_name : str, North : int, South : int, East : int, West : int):
            to_remove = []
            for n in self.graph:

                if n[0] > South and n[0] < North and n[1] < East and n[1] > West:
                    print(country_name)
                    print(n)
                    location = geolocator.reverse((str(n[0]) + "," + str(n[1])), timeout=None)
                    if location is None:
                        print("No country found")
                        continue
                    address = location.raw['address']
                    country = address.get('country', '')
                    print(country)
                    if country in banned_countries:
                        to_remove.append(n)
                        print("BANNING AIRSPACE")
            for i in to_remove:
                self.graph.remove_node(i)
        lat_iter = -90
        lon_iter = -180
        #initialize points
        while lat_iter < 90:
            while lon_iter < 180:
                print(lat_iter)
                print(lon_iter)
                self.graph.add_node((lat_iter, lon_iter))
                #diagonal left below
                if lat_iter > -90 and lon_iter > -180:
                    edges_to_add.append([(lat_iter,lon_iter),(lat_iter - self.lat_dist, lon_iter - self.lon_dist), gd((lat_iter,lon_iter),(lat_iter - self.lat_dist, lon_iter - self.lon_dist)).km])
                #left
                if lon_iter > -180:
                    edges_to_add.append([(lat_iter,lon_iter),(lat_iter, lon_iter - self.lon_dist), gd((lat_iter,lon_iter),(lat_iter, lon_iter - self.lon_dist)).km])
                #below
                if lat_iter > -90:
                    edges_to_add.append([(lat_iter,lon_iter),(lat_iter - self.lat_dist, lon_iter), gd((lat_iter,lon_iter),(lat_iter - self.lat_dist, lon_iter)).km])
                lon_iter += self.lon_dist
            lon_iter = -180
            lat_iter += self.lat_dist
        #Connecting the IDL:
        lon_iter = 180 - self.lon_dist
        lat_iter = -90 + self.lat_dist
        while lat_iter < 90:
            #right
            edges_to_add.append([(lat_iter,lon_iter),(lat_iter, -180), gd((lat_iter,lon_iter),(lat_iter, -180)).km])
            #upper right
            edges_to_add.append([(lat_iter,lon_iter),(lat_iter + self.lat_dist, -180), gd((lat_iter,lon_iter),(lat_iter + self.lat_dist, -180)).km])
            #lower right
            edges_to_add.append([(lat_iter,lon_iter),(lat_iter - self.lat_dist, -180), gd((lat_iter,lon_iter),(lat_iter - self.lat_dist, -180)).km])
            lat_iter += self.lat_dist
        #add all the edge weights
        self.graph.add_weighted_edges_from(edges_to_add)
        #remove edges in restricted airspace
        #banned_countries = ["Afghanistan", "Belarus", "Iran", "Iraq", "North Korea", "Libya", "Mali", "Россия", "Somalia", "Syria", "Ukraine", "Venezuela", "Yemen"]
        #Afghanistan
        scan_country("Afghanistan", 39, 28, 76, 60)
        #Belarus
        scan_country("Belarus", 57, 52, 32, 23)
        #Iran
        scan_country("Iran", 40, 26, 63, 44)
        #Iraq
        scan_country("Iraq", 38, 27, 48, 38)
        #North Korea
        scan_country("North Korea", 44, 38, 130, 124)
        #Libya
        scan_country("Libya", 34, 19, 26, 9)
        #Mali
        scan_country("Mali", 26, 10, 5, 12)
        #Russia
        scan_country("Russia", 82, 41, 179, 26)
        #Somalia
        scan_country("Somalia", 12, 1, 52, 41)
        #Syria
        scan_country("Syria", 38, 32, 44, 35)
        #Ukraine
        scan_country("Ukraine", 53, 44, 45, 22)
        #Venezuela
        scan_country("Venezuela", 16, 0, -60, -74)
        #Yemen
        scan_country("Yemen", 19, 12, 54, 41)

        


if __name__ == "__main__":
    test = WorldGraph("static/Graph1dist.txt")
    print(test.predict_trajectory("LHR","JFK"))
#test.save_graph("teststorage2.txt")
#print(test.predict_trajectory((37,-79),'UCFP'))
#b = nx.read_weighted_edgelist("Graph5dist.txt", "#", "_", nx.Graph, tuple, "utf-8")
#print(b)
#a = WorldGraph()