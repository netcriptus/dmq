import json
import random

from PyQt6.QtWidgets import (
    QComboBox,
    QGridLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from .constants import DRUGS_REGISTRY, SITUATIONS_REGISTRY
from .helpers import (
    CheckableComboBox,
    check_answer,
    make_float,
    read_current_drugs,
    read_current_situations,
    units,
)


def _create_unit_box():
    unit = QComboBox()
    unit.addItems(units)
    return unit


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


class StartMenu(QVBoxLayout):
    def __init__(self):
        super().__init__()
        self.random_quiz = QPushButton("Start quiz with random substances")
        self.choice_quiz = QPushButton("Start quiz with chosen substances")
        self.situation_quiz = QPushButton("Start quiz with situations")
        self.register_drug = QPushButton("Register substances")
        self.register_situation = QPushButton("Register situations")

        all_buttons = [
            self.random_quiz,
            self.choice_quiz,
            self.situation_quiz,
            self.register_drug,
            self.register_situation,
        ]

        for button in all_buttons:
            self.addWidget(button)


class RegisterDrugs(QGridLayout):
    def __init__(self):
        super().__init__()
        current_drugs = read_current_drugs()

        labels = ["Substance Name", "Unit", "Minimum dose", "Maximum dose"]
        for i, label in enumerate(labels):
            self.addWidget(QLabel(label), 0, i)

        for drug, info in current_drugs.items():
            line = self._create_form_line()
            self._fill_up_line(line, drug, info)
            self._add_line(line)

        line = self._create_form_line()
        self._add_line(line)

        self.save_button = QPushButton("Save")
        self.add_new_line_button = QPushButton("Add new line")
        self.add_new_line_button.clicked.connect(
            lambda: self._add_line(self._create_form_line())
        )
        self.cancel_button = QPushButton("Cancel")

    def _create_form_line(self):
        name = QLineEdit()
        unit = _create_unit_box()
        min_dose = QLineEdit()
        max_dose = QLineEdit()
        return name, unit, min_dose, max_dose

    def _fill_up_line(self, line, drug, info):
        line[0].setText(drug)
        line[1].setCurrentText(info["unit"])
        line[2].setText(str(info["min_dose"]))
        line[3].setText(str(info["max_dose"]))

    def _add_line(self, line):
        index = self.rowCount() + 1
        for i in range(len(line)):
            self.addWidget(line[i], index, i)

    def save(self):
        drugs = {}
        for i in range(1, self.rowCount()):
            if (
                self.itemAtPosition(i, 0) is None
                or not self.itemAtPosition(i, 0).widget().text()
            ):
                continue
            name = self.itemAtPosition(i, 0).widget().text()
            drugs[name] = {
                "unit": self.itemAtPosition(i, 1).widget().currentText(),
                "min_dose": make_float(self.itemAtPosition(i, 2).widget().text()),
                "max_dose": make_float(self.itemAtPosition(i, 3).widget().text()),
            }

        with open(DRUGS_REGISTRY, "w") as f:
            f.write(json.dumps(drugs))


class RegisterSituation(QGridLayout):
    def __init__(self):
        super().__init__()
        current_drugs = read_current_drugs()
        current_situations = read_current_situations()
        labels = ["Situation description", "Drugs"]
        for i, label in enumerate(labels):
            self.addWidget(QLabel(label), 0, i)

        index = 1

        for situation, drugs in current_situations:
            description = QTextEdit()
            description.setText(situation)
            drugs_states = []
            for d in current_drugs:
                drugs_states.append(d in drugs)

            drugs_box = CheckableComboBox()
            drugs_box.addItems(current_drugs, drugs_states)

            self.addWidget(description, index, 0)
            self.addWidget(drugs_box, index, 1)
            index += 1

        self.add_line(current_drugs)

        self.save_button = QPushButton("Save")
        self.save_button.clicked.connect(self.save)
        self.add_new_line_button = QPushButton("Add new line")
        self.add_new_line_button.clicked.connect(lambda: self.add_line(current_drugs))
        self.cancel_button = QPushButton("Cancel")

    def add_line(self, current_drugs):
        index = self.rowCount() + 1
        situation = QTextEdit()
        drugs = CheckableComboBox()
        drugs.addItems(current_drugs)
        self.addWidget(situation, index, 0)
        self.addWidget(drugs, index, 1)
        index += 1

    def save(self):
        situations = []
        for i in range(1, self.rowCount()):
            if (
                self.itemAtPosition(i, 0) is None
                or not self.itemAtPosition(i, 0).widget().toPlainText()
            ):
                continue
            situation = self.itemAtPosition(i, 0).widget().toPlainText()
            drugs = self.itemAtPosition(i, 1).widget().currentData()
            situations.append((situation, drugs))

        with open(SITUATIONS_REGISTRY, "w") as f:
            f.write(json.dumps(situations))


class SituationQuiz(QGridLayout):
    def __init__(self):
        super().__init__()
        current_situations = read_current_situations()
        current_drugs = read_current_drugs()
        current_drugs = list(current_drugs.keys())

        random_item = random.choice(current_situations)
        self.correct_answer = random_item[1]

        labels = ["Situation description", "Drugs"]
        for i, label in enumerate(labels):
            self.addWidget(QLabel(label), 0, i)
        description = QLabel(random_item[0])

        self.drugs_box = CheckableComboBox()
        self.drugs_box.addItems(current_drugs)

        self.addWidget(description, 1, 0)
        self.addWidget(self.drugs_box, 1, 1)

        self.answer_button = QPushButton("Answer")
        self.cancel_button = QPushButton("Cancel")

    def answer(self):
        answer = self.drugs_box.currentData()
        if self.correct_answer == answer:
            message = "Correct!"
        else:
            correct_answer = "\n".join(self.correct_answer)
            message = f"Incorrect.\nCorrect answer is:\n\n{correct_answer}"
        self.answer_window = AnswerWindow(message)
        self.answer_window.show()


class DrugQuiz(QGridLayout):
    def __init__(self, drug, quiz_type):
        super().__init__()

        self.quiz_type = quiz_type
        self.drug = drug
        self.addWidget(QLabel("Substance name"), 0, 0)
        self.addWidget(QLabel(drug), 1, 0)

        self.addWidget(QLabel("Patient weight"), 0, 1)
        self.weigth = random.randint(40, 160)
        self.addWidget(QLabel(f"{self.weigth} kg"), 1, 1)

        self.addWidget(QLabel("Dose"), 0, 2)
        self.dose = QLineEdit()
        self.addWidget(self.dose, 1, 2)

        self.addWidget(QLabel("Unit"), 0, 3)
        self.unit = _create_unit_box()
        self.addWidget(self.unit, 1, 3)

        self.answer_button = QPushButton("Answer")
        self.cancel_button = QPushButton("Cancel")

    def answer(self):
        message = check_answer(
            self.drug, self.weigth, self.dose.text(), self.unit.currentText()
        )
        self.answer_window = AnswerWindow(message)
        self.answer_window.show()


class ChooseDrugQuiz(QVBoxLayout):
    def __init__(self):
        super().__init__()
        all_options = read_current_drugs()
        options = list(all_options.keys())

        self.combo_options = QComboBox()
        self.combo_options.addItems(options)
        self.addWidget(self.combo_options)

        self.start_button = QPushButton("Start quiz")
        self.cancel_button = QPushButton("Cancel")
