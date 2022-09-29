
import pandas as pd
from newsapi import NewsApiClient
from config import * 



def Newsapi_get(keyword):
    # Init
    newsapi = NewsApiClient(api_key=News_api_key)
    # /v2/everything
    all_articles = newsapi.get_everything(q=keyword,
                                          #sources='bbc-news,the-verge',
                                          #domains='bbc.co.uk,techcrunch.com',
                                          #from_param='2017-12-01',
                                          #to='2017-12-12',
                                          language='en',
                                          sort_by='relevancy')


    ## store into Dataframe
    df = pd.DataFrame(columns=column_name)
    try:
        for article in all_articles['articles']:
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
                    [keyword,'en','News Api','sort_by=\'relevancy\'']]]
            temp = pd.DataFrame(info, columns=column_name)
            df =  pd.concat([df,temp], ignore_index=True)
        return df


    except KeyError:
        print("No article found! for keyword:", keyword)
    return df


for keyword in keywords:
    ## Output into csv
    df = Newsapi_get(keyword)
    if(len(df) != 0):
        filepath =  "Data/"+keyword +"_Newsapi_" +str(today)+".csv"
        df.to_csv(filepath)  




# In[ ]:




