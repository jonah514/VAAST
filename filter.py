import pandas as pd

class Filter:

    dom = True
    inter = True
    mil = True
    commercial = True
    alt = [0, 100000]
    speed = [0, 2000]

    df = pd.DataFrame()

    MilitaryList = []
    with open(r'static/MilitaryListUpdated.txt') as f:
        MilitaryList = [line.rstrip('\n') for line in f]
    MilitaryList = set(MilitaryList)
    
    airport_codes = []
    with open(r'static/DomesticList.txt') as f:
        airport_codes = [line.rstrip('\n') for line in f]
    airport_codes = set(airport_codes)

    def __init__(self, dom, inter, mil, commercial, alt : tuple, speed : tuple):
        #creates fields for self
        self.dom = dom
        self.inter = inter
        self.mil = mil
        self.commercial = commercial
        
        if dom == "true":
            self.dom = True;
        elif dom == "false":
            self.dom = False;
        
        if inter == "true":
            self.inter = True;
        elif inter == "false":
            self.inter = False;
        
        if mil == "true":
            self.mil = True;
        elif mil == "false":
            self.mil = False;
        
        if commercial == "true":
            self.commercial = True;
        elif commercial == "false":
            self.commercial = False;

        self.alt = alt
        self.speed = speed 

    def plane_apply_filter(self, dataframe: pd.DataFrame):
        self.df = dataframe
        #filtering for alititude and speed first
        self.df = self.df[self.df['Altitude'].astype(float).between(self.alt[0], self.alt[1])]
        self.df = self.df[self.df['Speed'].astype(float).between(self.speed[0], self.speed[1])]

        if not self.dom and not self.inter :
            return None
        elif self.dom and not self.inter :
            self.df = self.df[self.df['Leaving_From'].isin(self.airport_codes)]
            self.df = self.df[self.df['Going_To'].isin(self.airport_codes)]
        elif not self.dom and self.inter:
            self.df = self.df[~self.df['Leaving_From'].isin(self.airport_codes)]
            self.df = self.df[~self.df['Going_To'].isin(self.airport_codes)]

        if not self.mil and not self.commercial :
            return None
        elif self.mil and not self.commercial :
            self.df = self.df[self.df['Equipment'].isin(self.MilitaryList)]
        elif not self.mil and self.commercial:
            self.df = self.df[~self.df['Equipment'].isin(self.MilitaryList)]
        
        return self.df
    
    def ship_apply_filter(self, dataframe: pd.DataFrame):
        self.df = dataframe
        self.df = self.df[self.df['Speed'].astype(float).between(self.speed[0], self.speed[1])]
        return self.df

