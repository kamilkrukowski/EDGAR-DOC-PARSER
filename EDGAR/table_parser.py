
import base64
from selenium import webdriver
from selenium.webdriver.common.by import By
import pandas as pd
import numpy as np
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.remote.webelement import WebElement 


def get_element_info(element: WebElement)-> list():
    return {"value": element.text,"location": element.location, "size": element.size}

def pause() -> None:
    programPause = input("Press the <ENTER> key to close the selenium webdriver...")
    

def border(elem, driver: webdriver, color:str = "red") -> None:
    driver.execute_script(f"arguments[0].setAttribute(arguments[1], arguments[2])", elem, "style", "padding: 1px; border: 2px solid "+color+"; display: inline-block")


    
def find_page_location(driver: webdriver) -> dict:
    page_breaks = driver.find_elements(By.TAG_NAME, 'hr')
    #print("length of page breaks",len(page_breaks))
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
