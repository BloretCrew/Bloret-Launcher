from PyQt5.QtWidgets import QComboBox

comboBox = QComboBox()

# 添加选项
items = ['shoko', '西宫硝子', '宝多六花', '小鸟游六花']
comboBox.addItems(items)

# 当前选项的索引改变信号
comboBox.currentIndexChanged.connect(lambda index: print(comboBox.currentText()))
