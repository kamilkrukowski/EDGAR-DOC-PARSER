
import base64
from selenium import webdriver
from selenium.webdriver.common.by import By
import pandas as pd
import numpy as np
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.remote.webelement import WebElement 
from collections import Counter
from datetime import datetime


def table_parsing_2022(found_table, table_is_numeric, driver):
    # create a list of numeric table. Each table has its correspond index to the found table.
    numeric_table = [{"index": index, "element": found_table[index]} for index, val in enumerate(table_is_numeric) if val == 0 ]
    # dictionary that store the range of y for each page
    page_location = find_page_location(driver) 

    #find table information
    for index, val in enumerate(numeric_table) :
        val["info"] = get_element_info(val["element"])
        page_num = get_page_number(page_location, val["element"])
        val["info"]["page_num"] = page_num 
        val["info"]["location"]["y"] -=  page_location[page_num][0]
    #find label information
    for table in numeric_table:
        table["annotation"] = get_annotated_label_from_table(driver, table, table["info"]["page_num"],page_location[table["info"]["page_num"]][0] )
        
    return numeric_table

def table_element_to_df_2022(table_WebElement):
    table_val, first_label_row = table_to_list_2022(table_WebElement)
    index_name, column_name_row,value_row = list_of_row_to_df_input_2022(table_val,first_label_row)
    column_name_row  = pd.MultiIndex.from_tuples(column_name_row)
    index_name = pd.MultiIndex.from_tuples(index_name)
    df = pd.DataFrame(value_row , index=index_name, columns=column_name_row)
    df_dropna = df.dropna(axis='columns', how ="all")
    
    return df_dropna   

#@func_running_time
def list_of_table_element_to_df_2022(numeric_table:list()):
    df_numeric_table = []
    for i in range(len(numeric_table)):
        df_numeric_table.append(table_element_to_df(numeric_table[i]["element"]))
    return df_numeric_table

#####################################################################################################################################################
#
#
#
#                                              Helper Function 
#
#
#
#
#####################################################################################################################################################
# a decorator to measure the time of a function
def func_running_time(func):
    def inner(*args, **kwargs):
        print(f'INFO Begin to run function: {func.__name__} …')
        time_start = datetime.now()
        res = func(*args, **kwargs)
        time_diff = datetime.now() - time_start
        print(f'INFO Finished running function: {func.__name__}, total: {time_diff.seconds}s')
        print()
        return res
    return inner

#@func_running_time
def table_to_list_2022(table):
    tr = table.find_elements(By.TAG_NAME, 'tr')
    colspan= tr[0].find_elements(By.TAG_NAME, 'td')[0].get_attribute("colspan")
    
    table_val = []
    label_index =  0
    found_label= False
    
    for index  in range(1,len(tr)):
        col_index = 0
        val = [None] * int(colspan)
        row = tr[index]
        
        if row.text in {""," "}:
            continue
        
        if (found_label==  False ):
            fraction = len(row.find_elements(By.TAG_NAME, 'ix:nonfraction'))
            if(fraction>0):
                found_label = index
            
        row = row.find_elements(By.TAG_NAME, 'td')
        
        for i, td in enumerate(row):
            if td == None:
                continue
            temp_colspan = td.get_attribute("colspan")
            
            if(td.text in {")","",'',"%","(","$"}): 
                val[col_index] = None
            else:
                val[col_index] = td.text.replace("\n", "").replace("( ", "")
            
            col_index = ( col_index + 1 ) if temp_colspan == None else ( col_index + int(temp_colspan) )
            
        label_index+= 1
        table_val.append(val)       
        
    return table_val, found_label


#@func_running_time
def list_of_row_to_df_input_2022(table_val, first_label_row):
    num_row = len(table_val)
    #get the index name
    index_name = []
    column_name_row = []
    value_row =[]
    #get the column name
    row_index_start = 0
    
    for index_col_name_row in range(num_row):
        temp_val = None
        row = table_val[index_col_name_row][1:]
        if(table_val[index_col_name_row][0] != None or first_label_row == index_col_name_row ):
            row_index_start = index_col_name_row
            break
        else:
            for i in range(len(row)):

                if row[i] != None:
                    row[i-1] = row[i] if i != 0 else row[i-1]
                    temp_val = row[i]

                else:
                    row[i] = temp_val
        column_name_row.append(row)
        
    #get the value
    column_name_row = list(zip(*column_name_row))
    max_type_column = len(Counter(column_name_row))
    for index_val_row in range(row_index_start,num_row):
        index_name.append((index_val_row-row_index_start,table_val[index_val_row][0]))
        value = table_val[index_val_row][1:]
        length_value = len(value)
       
        for i in range(0,length_value,int(np.ceil(length_value/max_type_column))):
            if(value[i] == None):
                for x in range(i+1,i + int(np.ceil(length_value/max_type_column)),1):
                    if(x >= len(row)):
                        continue
                    if (value[x] != None):
                        value[i],value[x] = value[x], None
                        continue
        value_row.append(value)
            
        
    return index_name, column_name_row,value_row
        
def get_element_info(element: WebElement)-> list():
    return {"value": element.text,"location": element.location, "size": element.size}
    

def border(elem, driver: webdriver, color:str = "red") -> None:
    driver.execute_script(f"arguments[0].setAttribute(arguments[1], arguments[2])", elem, "style", "padding: 1px; border: 2px solid "+color+"; display: inline-block")


    
def find_page_location(driver: webdriver) -> dict:
    page_breaks = driver.find_elements(By.TAG_NAME, 'hr')
    page_number = 1
    # get the range of y for page 1
    page_location = {page_number: [0,page_breaks[0].location["y"]]}
    next_page_start =  page_location[page_number][1] + 2  # plus 2 b/c page break height = 2
    
    # get the range of y for page 2 to  n-1 (n is the last page)
    for hr in page_breaks[1:]:
        page_number += 1
        page_location[page_number]= [next_page_start,hr.location["y"]]
        next_page_start =  page_location[page_number][1] + 2  # plus 2 b/c page break height = 2
    # get the range of y for last page
    page_number += 1
    page_location[page_number]= [next_page_start,float('inf')]
    return page_location

def get_page_number(page_location: dict,element: WebElement) -> int:
    element_y = element.location["y"]
    for i in range(1,len(page_location)+1):
        if( element_y > page_location[i][0] and element_y <page_location[i][1]):
            return i
        
    return None


def get_annotated_label_from_table(driver: webdriver, table: dict, page_num = float("inf"), page_num_y = 0 )-> dict:
    # find all the label element
    found_annotation = table["element"].find_elements(By.TAG_NAME, 'ix:nonnumeric')
    found_annotation += table["element"].find_elements(By.TAG_NAME, 'ix:nonfraction')
    
    # store its location
    annotations = []
    for val in found_annotation: 
        annotations.append({"element": val,"info":get_element_info(val)})
        ##add page number
        annotations[-1]["info"]["page_num"] = page_num
        ##calculate new x and new y base on page
        annotations[-1]["info"]["location"]["y"] -= page_num_y
    return annotations


<<<<<<< Updated upstream
    #find table information
    for index, val in enumerate(numeric_table) :
        val["info"] = get_element_info(val["element"])
        page_num = get_page_number(page_location, val["element"])
        val["info"]["page_num"] = page_num 
        val["info"]["location"]["y"] -=  page_location[page_num][0]
    #find label information
    for table in numeric_table:
        table["annotation"] = get_annotated_label_from_table(driver, table, table["info"]["page_num"],page_location[table["info"]["page_num"]][0] )
        
    return numeric_table
=======
>>>>>>> Stashed changes
