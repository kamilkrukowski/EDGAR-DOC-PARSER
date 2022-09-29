from config import * 




def GNews_get(keyword,api_key):
    link = "https://gnews.io/api/v4/search?q="+str(keyword)+ "&lang=en&token="+ str(api_key)
    raw_data = requests.get(link)
    df = pd.DataFrame(columns=column_name)
    try:
        all_articles = json.loads(raw_data.content.decode('utf-8'))['articles']

        
        for article in all_articles:
            publishedAt,date,time = article['publishedAt'],"",""
            if publishedAt != "":
                date = publishedAt[5:10]+"-"+ publishedAt[0:4]
                time = publishedAt[11:16]
            
            info = [[date,
                    time,
                    article['title'],
                    article['description'],
                    article['content'],
                    article['url'],
                    [keyword,'Gnews Api',"lang=en"]]]
            temp = pd.DataFrame(info, columns=column_name)
            df =  pd.concat([df,temp], ignore_index=True)
        return df   
    except KeyError:
        print("No article found! for keyword:", keyword)
    return df


for keyword in keywords:
    ## Output into csv
    api_key= apikeys["Gnews_api_key"]
    df = GNews_get(keyword,api_key)
    if(len(df) != 0):
        if not os.path.exists("Data/GNewsapi/"+str(today)):
            os.makedirs("Data/GNewsapi/"+str(today))
        filepath =  "Data/GNewsapi/"+str(today)+"/"+keyword +"_GNewsapi_" +str(today)+".csv"
        df.to_csv(filepath)  

# In[ ]:




