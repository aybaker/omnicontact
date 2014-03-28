# -*- coding: utf-8 -*-
import xlrd


class ParserXls(object):
    value_list = []

    def read_file(self, file):
        workbook = xlrd.open_workbook(file_contents=file.read())
        worksheet = workbook.sheet_by_index(0)

        num_rows = worksheet.nrows - 1
        num_cells = worksheet.ncols - 1
        curr_row = -1

        while curr_row < num_rows:
            curr_row += 1
            curr_cell = -1

            while curr_cell < num_cells:
                curr_cell += 1
                cell_value = worksheet.cell_value(curr_row, curr_cell)

                if curr_cell == 0:
                    self.value_list.append(int(cell_value))

        return self.result()

    def result(self):
        return self.value_list
