from config import * 

def Newscatcher_get(keyword,api_key):
    url = "https://api.newscatcherapi.com/v2/search"
    querystring = {"q":"\""+ keyword+ "\"","lang":"en","sort_by":"relevancy","page":"1"}
    headers = {
        "x-api-key": api_key
    }
    raw_data = requests.request("GET", url, headers=headers, params=querystring)
    


    df = pd.DataFrame(columns=column_name)

    try:
        all_articles = json.loads(raw_data.content.decode('utf-8'))['articles']
        for article in all_articles:
            publishedAt,date,time = article['published_date'],"",""
            if publishedAt != "":
                date = publishedAt[5:10]+"-"+ publishedAt[0:4]
                time = publishedAt[11:16]
            
            info = [[date,
                    time,
                    article['title'],
                    article['excerpt'],
                    article['summary'],
                    article['link'],
                    [keyword,'Newscatcher Api',"lang=en"]]]
            temp = pd.DataFrame(info, columns=column_name)
            df =  pd.concat([df,temp], ignore_index=True)
        return df


    except KeyError:
        print("No article found! for keyword:", keyword)

    return df


for keyword in keywords:
    ## Output into csv
    api_key= apikeys["Newscatcher_api_key"]
    df = Newscatcher_get(keyword,api_key)
    if(len(df) != 0):
        if not os.path.exists("Data/Newscatcher/"+str(today)):
            os.makedirs("Data/Newscatcher/"+str(today))
        filepath =  "Data/Newscatcher/"+str(today)+"/"+keyword +"_Newscatcherapi_" +str(today)+".csv"
        df.to_csv(filepath)  




