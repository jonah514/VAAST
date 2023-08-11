VAAST Project Readme/Documentation

Introduction:
The purpose of this project is to track flights and ships and output potential points of interest/anomalies to the
user in order to aid in checking air/maritime space for national security purposes.

General program structure:
The application has three major components which all interact:
	-An AWS DynamoDB system which stores flight/ship data for use
	-A python backend which does most of the heavy computation (filtering, trajectory prediction, sending items
	 for display) and sends the returned values to the frontend via a flask framework. The main file of this
	 component is "framework.py"
	-An HTML/Javascript frontend which uses the leaflet library to display a map of all the planes/ships.
	 The main file of this component is "index.html"

Below are the specific roles of certain important files in the repository and their responsibilities/functions/how they collaborate:


DynamoDB Related:
lambda.py

Backend Related:
-filter.py:
	filter.py is a class file for creating a specific filter. A plane or ship dataframe can be filtered with the
	"plane_apply_filter" and "ship_apply_filter" functions, which will return a filtered dataframe.
-framework.py

	
-worldgraph.py
	worldgraph.py has two main purposes:
		-to create and save "worldgraphs", collections of nodes and edges for traversing the map in path
		 prediction functions, while avoiding banned airspace
		-to read in created worldgraphs and do trajectory prediction. Currently there are a few worldgraphs
		 in the repository, the best of these is "static/Graph1distEnhanced.txt", which has a resolution of 1 degree of
		 latitude and longitude and has 16 potential directions per point. However, booting up the website
		 and reading it in can take up to 30 seconds, so while testing other features it's best to use the
		 worse predicting graphs: "Graph1dist.txt" and "Graph2dist.txt"
		-to create a graph, do not enter a file path and just modify the latitude/longitude resolution global variables.A
		 Checking for banned airspace takes a long time with the API call we're using so expect a many hour process
		 to filter out banned airspace. 

-analysis_files/dissapearing_signal.py:
	

-analysis_files/patrolling_behavior.py:



Frontend Related:
-index.html
	-map sizing and position
        -filter bar sizing and positioning
-map.html
-style.css
	-styling on main page of website
-style.css1
	-styling for the links/pages on the website
