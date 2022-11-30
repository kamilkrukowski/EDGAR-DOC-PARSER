# unit test the new `parse_annotated_tables` against the old implementation
import sys; sys.path.append('..')
from EDGAR import parser
import os
# write the path of test html document below
file_path = os.path.join(os.path.dirname(__file__),'2022.html')


from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
import numpy as np
def old_func(self, driver_path: str, highlight: bool = False, save: bool = False, out_path: str = os.path.join('.','sample.htm')):

        # If path is None, stay on current document
        if driver_path is not None:
            self.driver.get(driver_path)

        found_table = self.driver.find_elements(By.TAG_NAME, 'table')

        table_is_numeric = np.zeros_like(found_table, 'int')# 0: numerical, 1: non-numerical, 2: unannotated
        for i in range(len(found_table)):
            table_is_numeric[i] = 2

            # If a table has both non-numeric and non-fraction, the non-fraction takes precedence
            try:
                found_numeric = found_table[i].find_element(By.TAG_NAME, 'ix:nonfraction')
                table_is_numeric[i] = 0
                continue;

            except NoSuchElementException:
                pass;

            try:
                found_numeric = found_table[i].find_element(By.TAG_NAME, 'ix:nonnumeric')
                table_is_numeric[i] = 1

            except NoSuchElementException:
                pass;
            
        for i in range(len(found_table)):
            if table_is_numeric[i] == 0:

                self._draw_border(found_table[i], 'green')
            elif table_is_numeric[i] == 1:
                self._draw_border(found_table[i], 'yellow')
            else:
                self._draw_border(found_table[i], 'pink')

        if save:
            self._save_driver_source(out_path)

        return found_table, table_is_numeric


    

p = parser(data_dir = 'edgar_downloads')
p.old_func = old_func


a2,b2 = p.old_func(p, driver_path = file_path, highlight = False)
a2_text = []
for i in range(len(a2)):
    a2_text += [a2[0].get_attribute('innerHTML')]
    
a1,b1 = p.parse_annotated_tables(driver_path = file_path, highlight = False)
a1_text = []
for i in range(len(a2)):
    a1_text += [a1[0].get_attribute('innerHTML')]
    
assert((b1 == b2).all())
assert(a1_text == a2_text)
print('the return list is same')
