import json
import os
from pathlib import Path

from PyQt6.QtCore import QEvent, Qt
from PyQt6.QtGui import QFontMetrics, QStandardItem
from PyQt6.QtWidgets import QComboBox, QStyledItemDelegate

HOME = Path.home()
APP_FOLDER = f"{HOME}/Library/DrugsQuiz"
DRUGS_REGISTRY = f"{APP_FOLDER}/drugs.json"

units = ["mg", "µg", "mg/kgKG", "µg/kgKG", "mg/kgKG/h", "µg/kgKG/h", "ml", "ml/kgKG"]


def make_float(string):
    return float(string.replace(",", "."))


def check_answer(drug, weigth, dose, unit):
    dose = make_float(dose)
    message = ""

    with open(DRUGS_REGISTRY, "r") as f:
        current_content = json.loads(f.read())
    info = current_content[drug]

    if info["unit"].endswith("KG"):
        info["unit"] = info["unit"].split("/")[0]

    if unit != info["unit"]:
        message += f'Wrong unit. The correct unit is {info["unit"]}\n'

    min_dose = make_float(info["min_dose"])
    max_dose = make_float(info["max_dose"])
    if not unit.endswith("/h"):
        min_dose *= weigth
        max_dose *= weigth

    if min_dose <= dose <= max_dose:
        message += "Correct dose!"
    else:
        message += f"Wrong dose. Correct answer is between {min_dose} and {max_dose}"
    return message


def ensure_file(file_path, empty_data):
    if not os.path.exists(file_path):
        with open(file_path, "w") as f:
            f.write(json.dumps(empty_data))


class CheckableComboBox(QComboBox):

    # Subclass Delegate to increase item height
    class Delegate(QStyledItemDelegate):
        def sizeHint(self, option, index):
            size = super().sizeHint(option, index)
            size.setHeight(20)
            return size

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Make the combo editable to set a custom text, but readonly
        self.setEditable(True)
        self.lineEdit().setReadOnly(True)

        # Use custom delegate
        self.setItemDelegate(CheckableComboBox.Delegate())

        # Update the text when an item is toggled
        self.model().dataChanged.connect(self.updateText)

        # Hide and show popup when clicking the line edit
        self.lineEdit().installEventFilter(self)
        self.closeOnLineEditClick = False

        # Prevent popup from closing when clicking on an item
        self.view().viewport().installEventFilter(self)

    def resizeEvent(self, event):
        # Recompute text to elide as needed
        self.updateText()
        super().resizeEvent(event)

    def eventFilter(self, object, event):

        if object == self.lineEdit():
            if event.type() == QEvent.Type.MouseButtonRelease:
                if self.closeOnLineEditClick:
                    self.hidePopup()
                else:
                    self.showPopup()
                return True
            return False

        if object == self.view().viewport():
            if event.type() == QEvent.Type.MouseButtonRelease:
                index = self.view().indexAt(event.pos())
                item = self.model().item(index.row())

                if item.checkState() == Qt.CheckState.Checked:
                    item.setCheckState(Qt.CheckState.Unchecked)
                else:
                    item.setCheckState(Qt.CheckState.Checked)
                return True
        return False

    def showPopup(self):
        super().showPopup()
        # When the popup is displayed, a click on the lineedit should close it
        self.closeOnLineEditClick = True

    def hidePopup(self):
        super().hidePopup()
        # Used to prevent immediate reopening when clicking on the lineEdit
        self.startTimer(100)
        # Refresh the display text when closing
        self.updateText()

    def timerEvent(self, event):
        # After timeout, kill timer, and reenable click on line edit
        self.killTimer(event.timerId())
        self.closeOnLineEditClick = False

    def updateText(self):
        texts = []
        for i in range(self.model().rowCount()):
            if self.model().item(i).checkState() == Qt.CheckState.Checked:
                texts.append(self.model().item(i).text())
        text = ", ".join(texts)

        # Compute elided text (with "...")
        metrics = QFontMetrics(self.lineEdit().font())
        elidedText = metrics.elidedText(text, Qt.TextElideMode.ElideRight, self.lineEdit().width())
        self.lineEdit().setText(elidedText)

    def addItem(self, text, checked=False):
        item = QStandardItem()
        item.setText(text)
        item.setData(text)
        item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsUserCheckable)
        state = Qt.CheckState.Checked if checked else Qt.CheckState.Unchecked
        item.setData(state, Qt.ItemDataRole.CheckStateRole)
        self.model().appendRow(item)

    def addItems(self, texts, checkedlist=None):
        for i, text in enumerate(texts):
            try:
                checked = checkedlist[i]
            except (IndexError, TypeError):
                checked = False
            self.addItem(text, checked)

    def currentData(self):
        # Return the list of selected items data
        res = []
        for i in range(self.model().rowCount()):
            if self.model().item(i).checkState() == Qt.CheckState.Checked:
                res.append(self.model().item(i).data())
        return res
