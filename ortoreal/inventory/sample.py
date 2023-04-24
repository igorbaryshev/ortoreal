import xlsxwriter

workbook = xlsxwriter.Workbook('hello.xlsx')
worksheet = workbook.add_worksheet()

worksheet.write('A1', 'Hello world asdfasdfasdfasdfasdf')
worksheet.autofit()

workbook.close()
