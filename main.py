import os
import sys
import json
import random
from pathlib import Path
from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QHBoxLayout, QLineEdit, QGridLayout, QLabel, QComboBox, QStatusBar, QTextEdit
from PyQt6.QtCore import Qt

from helpers import units, check_answer, make_float, CheckableComboBox, ensure_file

HOME = Path.home()
APP_FOLDER=f"{HOME}/Library/DrugsQuiz"
DRUGS_REGISTRY = f"{APP_FOLDER}/drugs.json"
SITUATIONS_REGISTRY = f"{APP_FOLDER}/situations.json"

os.makedirs(APP_FOLDER, exist_ok=True)
ensure_file(DRUGS_REGISTRY, {})
ensure_file(SITUATIONS_REGISTRY, [])

class AnswerWindow(QWidget):
    def __init__(self, message):
        super().__init__()
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        self.label = QLabel(message)
        self.layout.addWidget(self.label)
        self.button = QPushButton("OK")
        self.button.clicked.connect(self.close)
        self.layout.addWidget(self.button)


# Subclass QMainWindow to customize your application's main window
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Drugs math quiz")
        self.widget = QWidget()
        self.draw_start_screen()

        # Set the central widget of the Window.
        self.setCentralWidget(self.widget)

    def _redraw_screen(self, layout):
        self.widget = QWidget()
        self.widget.setLayout(layout)
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.setCentralWidget(self.widget)
        self.show()

    def _create_unit_box(self):
        unit = QComboBox()
        unit.addItems(units)
        return unit

    def _create_form_line(self):
        name = QLineEdit()
        unit = self._create_unit_box()
        min_dose = QLineEdit()
        max_dose = QLineEdit()
        return name, unit, min_dose, max_dose

    def _fill_up_line(self, line, drug, info):
        line[0].setText(drug)
        line[1].setCurrentText(info['unit'])
        line[2].setText(info['min_dose'])
        line[3].setText(info['max_dose'])

    def _add_line(self, layout, line):
        index = layout.rowCount() + 1
        for i in range(len(line)):
            layout.addWidget(line[i], index, i)

    def draw_start_screen(self):
        start_menu = {
            "start_random_button": (QPushButton("Start quiz with random substances"), 'random_quiz'),
            "start_choice_button": (QPushButton("Choose substace and start quiz"), 'choose_quiz'),
            "situation_quiz_button": (QPushButton("Start quiz about situations"), "situation_quiz"),
            "register_button": (QPushButton("Register substance"), "draw_register_screen"),
            "register_situation_button": (QPushButton("Register situation"), "register_situation"),
        }

        layout = QVBoxLayout()
        for button, function in start_menu.values():
            if function:
                f = getattr(self, function)
                button.clicked.connect(f)
            layout.addWidget(button)
        self._redraw_screen(layout)

    def answer(self, drug, weigth, dose, unit, quiz_type='random'):
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBar.show()
        message = check_answer(drug, weigth, dose, unit)
        self.answer_window = AnswerWindow(message)
        self.answer_window.show()

        next_question_button = QPushButton('Next question')
        if quiz_type == 'random':
            next_question_button.clicked.connect(self.random_quiz)
        else:
            next_question_button.clicked.connect(lambda: self.draw_quiz_screen(drug))
        cancel_button = QPushButton('Cancel')
        cancel_button.clicked.connect(self.draw_start_screen)
        self.statusBar.addWidget(next_question_button)
        self.statusBar.addWidget(cancel_button)
        self.statusBar.show()

    def draw_quiz_screen(self, drug, quiz_type='random'):
        layout = QGridLayout()
        layout.addWidget(QLabel('Substance name'), 0, 0)
        layout.addWidget(QLabel(drug), 1, 0)

        layout.addWidget(QLabel('Patient weight'), 0, 1)
        weigth = random.randint(40, 160)
        layout.addWidget(QLabel(f'{weigth} kg'), 1, 1)

        layout.addWidget(QLabel('Dose'), 0, 2)
        dose = QLineEdit()
        layout.addWidget(dose, 1, 2)

        layout.addWidget(QLabel('Unit'), 0, 3)
        unit = self._create_unit_box()
        layout.addWidget(unit, 1, 3)

        answer_button = QPushButton('Answer')
        answer_button.clicked.connect(lambda: self.answer(drug, weigth, dose.text(), unit.currentText(), quiz_type))
        cancel_button = QPushButton('Cancel')
        cancel_button.clicked.connect(self.draw_start_screen)

        self._redraw_screen(layout)
        self.statusBar.addWidget(answer_button)
        self.statusBar.addWidget(cancel_button)
        self.statusBar.show()

    def random_quiz(self):
        with open(DRUGS_REGISTRY, 'r') as f:
            current_content = json.loads(f.read())
        random_item = random.choice(list(current_content.keys()))
        self.draw_quiz_screen(random_item)

    def choose_quiz(self):
        with open(DRUGS_REGISTRY, 'r') as f:
            current_content = json.loads(f.read())
        options = list(current_content.keys())
        layout = QVBoxLayout()
        combo_options = QComboBox()
        combo_options.addItems(options)
        layout.addWidget(combo_options)
        
        start_button = QPushButton('Start quiz')
        start_button.clicked.connect(lambda: self.draw_quiz_screen(combo_options.currentText(), quiz_type='choose'))
        cancel_button = QPushButton('Cancel')
        cancel_button.clicked.connect(self.draw_start_screen)
        layout.addWidget(start_button)
        layout.addWidget(cancel_button)
        
        self._redraw_screen(layout)

        

    def save_drugs(self, layout):
        drugs = {}
        for i in range(1, layout.rowCount()):
            if layout.itemAtPosition(i, 0) is None or not layout.itemAtPosition(i, 0).widget().text():
                continue
            name = layout.itemAtPosition(i, 0).widget().text()
            drugs[name] = {
                'unit': layout.itemAtPosition(i, 1).widget().currentText(),
                'min_dose': make_float(layout.itemAtPosition(i, 2).widget().text()),
                'max_dose': make_float(layout.itemAtPosition(i, 3).widget().text())
            }
            
        with open(DRUGS_REGISTRY, 'w') as f:
            f.write(json.dumps(drugs))
        self.draw_start_screen()

    def draw_register_screen(self):
        with open(DRUGS_REGISTRY, 'r') as f:
            current_content = json.loads(f.read())

        layout = QGridLayout()
        labels = ['Substance Name', 'Unit', 'Minimum dose', 'Maximum dose']
        for i, label in enumerate(labels):
            layout.addWidget(QLabel(label), 0, i)

        for drug, info in current_content.items():
            line = self._create_form_line()
            self._fill_up_line(line, drug, info)
            self._add_line(layout, line)

        line = self._create_form_line()
        self._add_line(layout, line)

        save_button = QPushButton('Save')
        save_button.clicked.connect(lambda: self.save_drugs(layout))
        add_new_line_button = QPushButton('Add new line')
        add_new_line_button.clicked.connect(lambda: self._add_line(layout, self._create_form_line()))
        cancel_button = QPushButton('Cancel')
        cancel_button.clicked.connect(self.draw_start_screen)

        self._redraw_screen(layout)
        self.statusBar.addWidget(add_new_line_button)
        self.statusBar.addWidget(save_button)
        self.statusBar.addWidget(cancel_button)
        self.statusBar.show()

    def save_situations(self, layout):
        situations = []
        for i in range(1, layout.rowCount()):
            if layout.itemAtPosition(i, 0) is None or not layout.itemAtPosition(i, 0).widget().toPlainText():
                continue
            situation = layout.itemAtPosition(i, 0).widget().toPlainText()
            drugs = layout.itemAtPosition(i, 1).widget().currentData()
            situations.append((situation, drugs))
            
        with open(SITUATIONS_REGISTRY, 'w') as f:
            f.write(json.dumps(situations))
        self.draw_start_screen()

    def register_situation(self):
        layout = QGridLayout()
        labels = ['Situation description', 'Drugs']
        for i, label in enumerate(labels):
            layout.addWidget(QLabel(label), 0, i)

        with open(SITUATIONS_REGISTRY, 'r') as f:
            current_content = json.loads(f.read())
        with open(DRUGS_REGISTRY, 'r') as f:
            current_drugs = json.loads(f.read())
            current_drugs = list(current_drugs.keys())

        index = 1

        def add_line(layout):
            nonlocal index
            situation = QTextEdit()
            drugs = CheckableComboBox()
            drugs.addItems(current_drugs)
            layout.addWidget(situation, index, 0)
            layout.addWidget(drugs, index, 1)
            index += 1

        for situation, drugs in current_content:
            description = QTextEdit()
            description.setText(situation)
            drugs_states = []
            for d in current_drugs:
                drugs_states.append(d in drugs)

            drugs_box = CheckableComboBox()
            drugs_box.addItems(current_drugs, drugs_states)

            layout.addWidget(description, index, 0)
            layout.addWidget(drugs_box, index, 1)
            index += 1

        add_line(layout)

        save_button = QPushButton('Save')
        save_button.clicked.connect(lambda: self.save_situations(layout))
        add_new_line_button = QPushButton('Add new line')
        add_new_line_button.clicked.connect(lambda: add_line(layout))
        cancel_button = QPushButton('Cancel')
        cancel_button.clicked.connect(self.draw_start_screen)

        self._redraw_screen(layout)
        self.statusBar.addWidget(add_new_line_button)
        self.statusBar.addWidget(save_button)
        self.statusBar.addWidget(cancel_button)
        self.statusBar.show()

    def answer_situation(self, correct_answer, answer):
        if correct_answer == answer:
            message = 'Correct!'
        else:
            correct_answer = '\n'.join(correct_answer)
            message = f"Incorrect.\nCorrect answer is:\n\n{correct_answer}"
        self.answer_window = AnswerWindow(message)
        self.answer_window.show()

        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)

        next_question_button = QPushButton('Next Question')
        next_question_button.clicked.connect(self.situation_quiz)
        cancel_button = QPushButton('Cancel')
        cancel_button.clicked.connect(self.draw_start_screen)

        self.statusBar.addWidget(next_question_button)
        self.statusBar.addWidget(cancel_button)
        self.statusBar.show()

    def situation_quiz(self):
        with open(SITUATIONS_REGISTRY, 'r') as f:
            current_content = json.loads(f.read())
        with open(DRUGS_REGISTRY, 'r') as f:
            current_drugs = json.loads(f.read())
            current_drugs = list(current_drugs.keys())

        random_item = random.choice(current_content)

        layout = QGridLayout()
        labels = ['Situation description', 'Drugs']
        for i, label in enumerate(labels):
            layout.addWidget(QLabel(label), 0, i)
        description = QLabel(random_item[0])

        drugs_box = CheckableComboBox()
        drugs_box.addItems(current_drugs)

        layout.addWidget(description, 1, 0)
        layout.addWidget(drugs_box, 1, 1)

        self._redraw_screen(layout)
        answer_button = QPushButton('Answer')
        answer_button.clicked.connect(lambda: self.answer_situation(random_item[1], drugs_box.currentData()))
        cancel_button = QPushButton('Cancel')
        cancel_button.clicked.connect(self.draw_start_screen)

        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBar.addWidget(answer_button)
        self.statusBar.addWidget(cancel_button)
        self.statusBar.show()



        
        


app = QApplication(sys.argv)

window = MainWindow()
window.show()

app.exec()
