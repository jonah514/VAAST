import tarfile
import pandas as pd
import xml.etree.ElementTree as ET
import os
import tempfile
from io import BytesIO

'''
code exactly as in the aws lambda function

untar and unzip files
parse each file. cleaning and filtering
handles plane or ship file of fr24 or intelliearth format
converts dataframe into csv and uploads to corresponding s3 bucket

NOTE: ship deletes many null rows. we did not see any use in keeping them
these rows contain small bits of data we deemed unnecessary
'''

#get the date, time_id from fr24 file
def multiple(ts,id):
    time = pd.to_datetime(ts, utc=True, unit='s')
    build = time.strftime('%H:%M:%S')
    time_id = f"{build}#{id}"
    date = time.strftime('%Y-%m-%d')
    return date,time_id

#get the date, time_id from intelliearth file (timestamp)
def multiple_S(ts,id):
    ts = ts.split('T')
    date = ts[0][0:4] + '-' +ts[0][4:6] + '-' + ts[0][6:8]
    ts = ts[1]
    build = ts[0:2]+':'+ts[2:4]+':'+ts[4:6]#10 for ms
    time_id = f"{build}#{id}"
    return date, time_id

#actual lambda function
def lambda_handler():
    with tempfile.TemporaryDirectory() as dir:
        print('handler initiated')
        bucket = event['Records'][0]['s3']['bucket']['name'] #name of bucket raw data pulled from
        key = event['Records'][0]['s3']['object']['key']     #key of raw data file
        print(bucket, key)
        #bucket to put extracted files in
        ship_bucket = 'extracted-vaast-ais-maritime'
        plane_bucket = 'extracted-vaast-adsb-air'
    
        unzipped = os.listdir(dir)
        print(f"TMP SIZE: {len(unzipped)}")
    
        input_tar_file = s3_client.get_object(Bucket = bucket, Key = key)
        input_tar_content = input_tar_file['Body'].read()
    
        file = tarfile.open(fileobj = BytesIO(input_tar_content))
        file.extractall(dir) #extracts all .txt files and temporarily stores them in lambda /tmp directory, which will need to be expanded to abt 2 GBs
        file.close()
    
        #reading all files from current unzipped directory into one dataframe
        #last of all .txt files extrated from tar.gz
        unzipped = os.listdir(dir)
        
    
        master = pd.DataFrame()
        temp = pd.DataFrame()
    
        #check file exists and contains fr24 in the name --- our files all did
        if file is not None and unzipped[0] is not None and 'fr24' in unzipped[0]:
            #iterate through files from tar.gz
            count = 0
            holder = []
            for this_file in unzipped:
                count +=1
                percent = int(round(count/len(unzipped), 2)*100)
                if (count % 100 == 0 and percent % 25 == 0) or count == len(unzipped) or count == 1:
                    print(f"{percent}% {count}/{len(unzipped)}")
                file_path = os.path.join(dir, this_file)  # Construct the absolute file path
                with open(file_path, 'r') as xml_file:
                    temp = pd.read_xml(xml_file, parser='etree')
                grouped = temp.mask(temp.eq('None')|temp.eq('NaN')).groupby('flight_id').first()
                grouped[['Date', 'Time_ID']] = grouped.apply(lambda x: multiple(x['timestamp'], x.name), axis=1,result_type='expand')
                holder.append(grouped)
                
            #print(f"Concatinating...")
            master = pd.concat(holder, axis=0)
            
            #print(f"Reset Index...")
            master = master.reset_index()
            
            #print(f"Dropping Columns...")
            dropped = master[['Date','Time_ID','latitude','longitude','altitude','speed','heading','equipment', 'flight', 'registration', 'schd_from', 'schd_to']]
            dropped = dropped.rename(columns= {'latitude': "Latitude", 'longitude':'Longitude', 'altitude':'Altitude', 'speed':'Speed',\
                'heading':'Heading','equipment':'Equipment', 'flight':'Flight', 'registration':'Registration', 'schd_from':'Going_To', 'schd_to':'Leaving_From'})
                
            #NOTE: columns: Going_To and Leaving_From are flipped. keeping this way for continuity
    
        else:
            #iterate through files from tar.gz
            count = 0
            holder = []
            for this_file in unzipped:
                count +=1
                percent = int(round(count/len(unzipped), 4)*100)
                if (count % 100 == 0 and percent % 25 == 0) or count == len(unzipped) or count == 1:
                    print(f"{percent}% {count}/{len(unzipped)}")
                file_path = os.path.join(dir, this_file)  # Construct the absolute file path
                with open(file_path, 'r') as xml_file:
                    temp = pd.read_xml(xml_file, parser='etree')
                #drop nan position rows
                try:
                    temp = temp[temp['position_lat'].notna()]
                except:
                    pass
                temp[['Date', 'Time_ID']] = temp.apply(lambda x: multiple_S(x['timestamp'], x['mmsi']), axis=1,result_type='expand')
                holder.append(temp)
            print(f"Concatinating...")
            master = pd.concat(holder, axis = 0)
            
            print(f"Dropping Columns...")
            dropped = master[['Date', 'Time_ID','position_lon','position_lat','sog','cog','nav_stat']]
            dropped = dropped.rename(columns= {'position_lat': "Latitude", 'position_lon':'Longitude', 'sog':'Speed',\
                'nav_stat':'Nav_Status','cog':'Heading'})
            #NOTE: for some reason nav_stat is not getting read in. not a big deal with our implementation
    
    
        #converting dataframe to csv string object and uploading to new bucket
        #print(f"ToCSV...")
        dropped_csv = dropped.to_csv(dir+"/csv_file.txt", index=False)
        
        #print(f"Upload...")
        #upload csv to s3 with the same name it began with except .csv at end
        if 'fr24' in unzipped[0]:
            s3_client.upload_file(dir+"/csv_file.txt", plane_bucket, f"{key[:len(key)-7]}.csv")
        else:
            s3_client.upload_file(dir+"/csv_file.txt", ship_bucket, f"{key[:len(key)-7]}.csv")
